# src/orchestrator_enhanced.py
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import asyncio
from uuid import UUID

from src.orchestrator import EventOrchestrator
from src.roles.registry import RoleRegistry, RoleConfiguration
from src.enrichment.mitre_attack import MITREATTACKEnricher

@dataclass
class AnalysisConfiguration:
    """Configuration for the multi-agent analysis"""
    role_names: List[str] = None
    enable_mitre_enrichment: bool = False
    enable_confidence_calibration: bool = True
    convergence_thresholds: Dict[str, float] = None
    max_retries: int = 3
    temperature: float = 0.1
    
    def __post_init__(self):
        if self.role_names is None:
            self.role_names = ["benign", "malicious", "skeptic"]
        
        if self.convergence_thresholds is None:
            self.convergence_thresholds = {
                "consensus_threshold": 0.2,
                "jaccard_threshold": 0.2,
                "residual_disagreement_threshold": 0.35
            }

class EnhancedOrchestrator(EventOrchestrator):
    """Enhanced orchestrator with pluggable components"""
    
    def __init__(self, config: AnalysisConfiguration = None, storage_path: Optional[str] = None):
        if config is None:
            config = AnalysisConfiguration()
        
        self.config = config
        self.role_registry = RoleRegistry()
        self.mitre_enricher = MITREATTACKEnricher() if config.enable_mitre_enrichment else None
        
        # Load custom roles if specified
        self._load_custom_roles()
        
        # Initialize with configured roles
        super().__init__(storage_path)
        
        # Override agent creation with configured roles
        self.agents = self._create_agents_from_roles()
    
    def _load_custom_roles(self):
        """Load custom roles from configuration"""
        # Example: Load from environment variable or config file
        custom_role_module = None  # Could be from config
        if custom_role_module:
            self.role_registry.load_from_module(custom_role_module)
    
    def _create_agents_from_roles(self) -> Dict[str, Any]:
        """Create agents based on configured roles"""
        agents = {}
        
        for role_name in self.config.role_names:
            role_config = self.role_registry.get(role_name)
            if not role_config:
                print(f"[EnhancedOrchestrator] Role {role_name} not found, skipping")
                continue
            
            # Create agent with role-specific configuration
            # (Assuming BaseAgent accepts role configuration)
            agent = self._create_agent(role_config)
            agents[role_name] = agent
        
        return agents
    
    def _create_agent(self, role_config: RoleConfiguration):
        """Create an agent instance from role configuration"""
        # This would need integration with the BaseAgent class
        # For now, using a simplified approach
        from src.agents.base_agent import BaseAgent
        
        class ConfigurableAgent(BaseAgent):
            def __init__(self, config: RoleConfiguration):
                super().__init__(config.name)
                self.role_config = config
            
            def get_system_prompt_evidence(self) -> str:
                return self.role_config.system_prompt_evidence
            
            def get_system_prompt_claims(self) -> str:
                return self.role_config.system_prompt_claims
        
        return ConfigurableAgent(role_config)
    
    async def analyze_incident_enhanced(self, incident_text: str, 
                                       event_id: Optional[UUID] = None) -> Dict:
        """Enhanced analysis with optional MITRE enrichment"""
        # Run standard analysis
        result = await super().analyze_incident(incident_text, event_id)
        
        # Apply MITRE enrichment if enabled
        if self.mitre_enricher:
            result = await self._enrich_with_mitre(result)
        
        # Apply confidence calibration if enabled
        if self.config.enable_confidence_calibration:
            result = self._calibrate_confidence(result)
        
        return result
    
    async def _enrich_with_mitre(self, analysis_result: Dict) -> Dict:
        """Enrich analysis with MITRE ATT&CK context"""
        event_id = analysis_result['event_id']
        event_dir = Path(self.storage_path) / event_id
        
        # Load evidence artifacts
        evidence_files = list(event_dir.glob("evidence_*.json"))
        enriched_evidence = {}
        
        for evidence_file in evidence_files:
            with open(evidence_file, 'r') as f:
                evidence_data = json.load(f)
            
            # Enrich evidence items
            enriched_items = self.mitre_enricher.enrich_evidence(evidence_data['evidence'])
            evidence_data['evidence'] = enriched_items
            
            # Save enriched evidence
            enriched_file = evidence_file.with_name(f"enriched_{evidence_file.name}")
            with open(enriched_file, 'w') as f:
                json.dump(evidence_data, f, indent=2)
            
            # Generate ATT&CK matrix
            if enriched_items:
                attack_matrix = self.mitre_enricher.generate_attack_matrix(enriched_items)
                
                # Save attack matrix
                matrix_file = event_dir / f"attack_matrix_{evidence_file.stem}.json"
                with open(matrix_file, 'w') as f:
                    json.dump(attack_matrix, f, indent=2)
                
                enriched_evidence[evidence_data['agent_id']] = {
                    'enriched_count': len(enriched_items),
                    'attack_techniques': len(attack_matrix),
                    'matrix_file': str(matrix_file.name)
                }
        
        # Add MITRE context to final result
        analysis_result['mitre_enrichment'] = {
            'enabled': True,
            'agents_enriched': enriched_evidence,
            'total_techniques_identified': sum(
                info['attack_techniques'] for info in enriched_evidence.values()
            )
        }
        
        return analysis_result
    
    def _calibrate_confidence(self, analysis_result: Dict) -> Dict:
        """Apply confidence calibration based on historical performance"""
        # Simplified calibration - in production, use historical data
        decision = analysis_result['decision']
        residual = analysis_result['summary']['residual_disagreement']
        
        # Apply calibration formula
        calibrated_confidence = decision['confidence'] * (1 - 0.3 * residual)
        decision['confidence'] = max(0.0, min(1.0, calibrated_confidence))
        
        # Add calibration note
        if 'reason_codes' not in decision:
            decision['reason_codes'] = []
        decision['reason_codes'].append('CONFIDENCE_CALIBRATED')
        
        return analysis_result