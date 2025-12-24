# src/enrichment/mitre_attack.py
import requests
from typing import List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime

class MITREATTACKEnricher:
    """Enrich evidence with MITRE ATT&CK framework mappings"""
    
    def __init__(self, cache_dir: Path = Path("./cache/mitre")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load MITRE ATT&CK data
        self.techniques = self._load_mitre_data()
        
        # Mapping from evidence types to ATT&CK techniques
        self.evidence_mappings = {
            'command_line': ['T1059', 'T1064'],  # Command and Scripting Interpreter
            'process': ['T1057', 'T1047'],       # Process Discovery, Windows Management Instrumentation
            'registry': ['T1112'],               # Modify Registry
            'file_path': ['T1005'],              # Data from Local System
            'network_flow': ['T1043', 'T1071'],  # Commonly Used Port, Standard Application Layer Protocol
            'user': ['T1078'],                   # Valid Accounts
            'behavior': ['T1204']                # User Execution
        }
    
    def _load_mitre_data(self) -> Dict:
        """Load MITRE ATT&CK data from local cache or API"""
        cache_file = self.cache_dir / "techniques.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Fetch from MITRE ATT&CK API
        try:
            response = requests.get(
                "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
            )
            data = response.json()
            
            # Extract techniques
            techniques = {}
            for obj in data['objects']:
                if obj['type'] == 'attack-pattern' and 'external_references' in obj:
                    # Get MITRE ID
                    for ref in obj['external_references']:
                        if ref['source_name'] == 'mitre-attack':
                            mitre_id = ref['external_id']
                            techniques[mitre_id] = {
                                'id': mitre_id,
                                'name': obj.get('name', ''),
                                'description': obj.get('description', ''),
                                'tactics': [phase['phase_name'] for phase in obj.get('kill_chain_phases', [])],
                                'platforms': obj.get('x_mitre_platforms', []),
                                'data_sources': obj.get('x_mitre_data_sources', [])
                            }
                            break
            
            # Cache the data
            with open(cache_file, 'w') as f:
                json.dump(techniques, f, indent=2)
            
            return techniques
            
        except Exception as e:
            print(f"[MITRE] Failed to load MITRE data: {e}")
            return {}
    
    def enrich_evidence(self, evidence_items: List[Dict]) -> List[Dict]:
        """Enrich evidence items with MITRE ATT&CK context"""
        enriched_items = []
        
        for item in evidence_items:
            enriched_item = item.copy()
            enriched_item['mitre_context'] = []
            
            # Check for MITRE mappings based on evidence type
            evidence_type = item.get('type')
            if evidence_type in self.evidence_mappings:
                technique_ids = self.evidence_mappings[evidence_type]
                for tech_id in technique_ids:
                    if tech_id in self.techniques:
                        technique = self.techniques[tech_id]
                        enriched_item['mitre_context'].append({
                            'technique_id': tech_id,
                            'technique_name': technique['name'],
                            'tactics': technique['tactics'],
                            'relevance_score': self._calculate_relevance(item, technique)
                        })
            
            # Also check value-based mappings (e.g., specific commands)
            if 'value' in item:
                value_mappings = self._map_value_to_techniques(item['value'])
                enriched_item['mitre_context'].extend(value_mappings)
            
            # Deduplicate and sort by relevance
            if enriched_item['mitre_context']:
                # Remove duplicates
                seen = set()
                unique_context = []
                for ctx in enriched_item['mitre_context']:
                    key = ctx['technique_id']
                    if key not in seen:
                        seen.add(key)
                        unique_context.append(ctx)
                
                # Sort by relevance
                enriched_item['mitre_context'] = sorted(
                    unique_context, 
                    key=lambda x: x['relevance_score'], 
                    reverse=True
                )[:3]  # Keep top 3 most relevant
            
            enriched_items.append(enriched_item)
        
        return enriched_items
    
    def _calculate_relevance(self, evidence: Dict, technique: Dict) -> float:
        """Calculate relevance score between evidence and technique"""
        score = 0.0
        
        # Type-based relevance
        evidence_type = evidence.get('type', '')
        if evidence_type in ['command_line', 'process']:
            if 'Execution' in technique.get('tactics', []):
                score += 0.3
        elif evidence_type in ['network_flow']:
            if 'Command and Control' in technique.get('tactics', []):
                score += 0.3
        
        # Value-based heuristic matching
        value = evidence.get('value', '').lower()
        
        # Common malware indicators
        malware_indicators = ['powershell', 'cmd', 'wmic', 'schtasks', 'regsvr32']
        if any(indicator in value for indicator in malware_indicators):
            if 'Execution' in technique.get('tactics', []):
                score += 0.2
        
        # Persistence indicators
        persistence_indicators = ['run', 'startup', 'service', 'scheduled']
        if any(indicator in value for indicator in persistence_indicators):
            if 'Persistence' in technique.get('tactics', []):
                score += 0.2
        
        # Defense evasion indicators
        evasion_indicators = ['bypass', 'disable', 'evade', 'obfuscate']
        if any(indicator in value for indicator in evasion_indicators):
            if 'Defense Evasion' in technique.get('tactics', []):
                score += 0.2
        
        return min(score, 1.0)
    
    def _map_value_to_techniques(self, value: str) -> List[Dict]:
        """Map specific values to MITRE techniques"""
        value_lower = value.lower()
        mappings = []
        
        # Common command patterns to MITRE techniques
        command_patterns = {
            'T1059': ['powershell', 'cmd.exe', 'bash', 'sh'],  # Command and Scripting Interpreter
            'T1547': ['reg add', 'regedit', 'registry'],       # Boot or Logon Autostart Execution
            'T1053': ['schtasks', 'crontab', 'at'],            # Scheduled Task/Job
            'T1106': ['rundll32', 'regsvr32'],                 # Native API
            'T1220': ['xcopy', 'robocopy'],                    # XSL Script Processing
        }
        
        for technique_id, patterns in command_patterns.items():
            if any(pattern in value_lower for pattern in patterns):
                if technique_id in self.techniques:
                    technique = self.techniques[technique_id]
                    mappings.append({
                        'technique_id': technique_id,
                        'technique_name': technique['name'],
                        'tactics': technique['tactics'],
                        'relevance_score': 0.8  # High relevance for pattern matches
                    })
        
        return mappings
    
    def generate_attack_matrix(self, enriched_evidence: List[Dict]) -> Dict:
        """Generate MITRE ATT&CK matrix visualization data"""
        tactics = {}
        
        for item in enriched_evidence:
            for ctx in item.get('mitre_context', []):
                for tactic in ctx.get('tactics', []):
                    if tactic not in tactics:
                        tactics[tactic] = []
                    
                    tactics[tactic].append({
                        'technique_id': ctx['technique_id'],
                        'technique_name': ctx['technique_name'],
                        'evidence_value': item.get('value', ''),
                        'evidence_type': item.get('type', ''),
                        'relevance': ctx['relevance_score']
                    })
        
        # Sort tactics and techniques
        sorted_tactics = {}
        for tactic in sorted(tactics.keys()):
            # Deduplicate techniques within tactic
            seen_techniques = set()
            unique_techniques = []
            for tech in tactics[tactic]:
                if tech['technique_id'] not in seen_techniques:
                    seen_techniques.add(tech['technique_id'])
                    unique_techniques.append(tech)
            
            # Sort by relevance
            sorted_tactics[tactic] = sorted(
                unique_techniques, 
                key=lambda x: x['relevance'], 
                reverse=True
            )
        
        return sorted_tactics