# src/replay/replay_engine.py
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import hashlib

from src.schemas.evidence import EvidenceExtraction
from src.schemas.claims import AgentClaims
from src.schemas.convergence import ConvergenceMetrics, FinalLabel
from src.convergence_engine import ConvergenceEngine

class ArtifactReplayEngine:
    """Replay system for deterministic recomputation from stored artifacts"""
    
    def __init__(self, artifacts_base_path: Path):
        self.artifacts_base_path = Path(artifacts_base_path)
        self.convergence_engine = ConvergenceEngine()
        
    def find_event_directories(self) -> List[Path]:
        """Find all event directories in artifacts base path"""
        event_dirs = []
        for item in self.artifacts_base_path.iterdir():
            if item.is_dir() and len(item.name) == 36:  # UUID length
                try:
                    # Check if it's a valid UUID
                    import uuid
                    uuid.UUID(item.name)
                    event_dirs.append(item)
                except ValueError:
                    continue
        return sorted(event_dirs, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def load_event_artifacts(self, event_dir: Path) -> Optional[Dict]:
        """Load all artifacts for a specific event"""
        event_id = event_dir.name
        
        # Check for required artifacts
        evidence_files = list(event_dir.glob("evidence_*.json"))
        claims_files = list(event_dir.glob("claims_*.json"))
        convergence_files = list(event_dir.glob("convergence_*.json"))
        
        if not evidence_files or not claims_files:
            return None
        
        # Load incident text
        incident_path = event_dir / "incident.txt"
        if not incident_path.exists():
            return None
        
        with open(incident_path, 'r') as f:
            incident_text = f.read()
        
        # Load evidence extractions
        evidence_extractions = {}
        for evidence_file in evidence_files:
            try:
                with open(evidence_file, 'r') as f:
                    data = json.load(f)
                # Extract agent_id from filename (evidence_benign_2024-01-01T12:00:00.json)
                filename = evidence_file.name
                agent_id = filename.split('_')[1]  # 'evidence_{agent_id}_{timestamp}.json'
                
                evidence = EvidenceExtraction(**data)
                evidence_extractions[agent_id] = evidence
            except Exception as e:
                print(f"Error loading evidence file {evidence_file}: {e}")
                continue
        
        # Load agent claims
        agent_claims = {}
        for claims_file in claims_files:
            try:
                with open(claims_file, 'r') as f:
                    data = json.load(f)
                agent_id = claims_file.name.split('_')[1]
                
                claims = AgentClaims(**data)
                agent_claims[agent_id] = claims
            except Exception as e:
                print(f"Error loading claims file {claims_file}: {e}")
                continue
        
        # Load convergence metrics (if exists)
        convergence_metrics = None
        if convergence_files:
            try:
                with open(convergence_files[0], 'r') as f:
                    data = json.load(f)
                convergence_metrics = ConvergenceMetrics(**data)
            except Exception as e:
                print(f"Error loading convergence file: {e}")
        
        return {
            'event_id': event_id,
            'incident_text': incident_text,
            'evidence_extractions': evidence_extractions,
            'agent_claims': agent_claims,
            'convergence_metrics': convergence_metrics,
            'artifact_files': {
                'evidence': [str(f) for f in evidence_files],
                'claims': [str(f) for f in claims_files],
                'convergence': [str(f) for f in convergence_files]
            }
        }
    
    def replay_event(self, event_id: str, recalculate: bool = True) -> Dict:
        """Replay an event's analysis from stored artifacts"""
        event_dir = self.artifacts_base_path / event_id
        if not event_dir.exists():
            raise ValueError(f"Event directory not found: {event_dir}")
        
        # Load artifacts
        artifacts = self.load_event_artifacts(event_dir)
        if not artifacts:
            raise ValueError(f"Could not load artifacts for event: {event_id}")
        
        if not recalculate and artifacts['convergence_metrics']:
            # Return existing convergence metrics
            return {
                'event_id': event_id,
                'status': 'loaded_from_storage',
                'convergence_metrics': artifacts['convergence_metrics'],
                'evidence_extractions': artifacts['evidence_extractions'],
                'agent_claims': artifacts['agent_claims'],
                'incident_text_preview': artifacts['incident_text'][:500]
            }
        
        # Recompute convergence metrics deterministically
        if (len(artifacts['evidence_extractions']) < 2 or 
            len(artifacts['agent_claims']) < 2):
            raise ValueError(f"Insufficient artifacts for event: {event_id}")
        
        # Recompute convergence
        convergence_metrics = self.convergence_engine.compute_convergence(
            artifacts['evidence_extractions'],
            artifacts['agent_claims']
        )
        
        # Save recomputed metrics
        timestamp = datetime.utcnow().isoformat()
        replay_file = event_dir / f"convergence_replay_{timestamp}.json"
        with open(replay_file, 'w') as f:
            f.write(convergence_metrics.model_dump_json(indent=2))
        
        # Compare with original (if exists)
        comparison = None
        if artifacts['convergence_metrics']:
            comparison = self._compare_convergence_results(
                original=artifacts['convergence_metrics'],
                recomputed=convergence_metrics
            )
        
        return {
            'event_id': event_id,
            'status': 'recomputed',
            'convergence_metrics': convergence_metrics,
            'evidence_extractions_count': len(artifacts['evidence_extractions']),
            'agent_claims_count': len(artifacts['agent_claims']),
            'replay_file': str(replay_file),
            'comparison_with_original': comparison,
            'deterministic_check': comparison['identical'] if comparison else 'no_original'
        }
    
    def _compare_convergence_results(self, original: ConvergenceMetrics, 
                                   recomputed: ConvergenceMetrics) -> Dict:
        """Compare original and recomputed convergence metrics"""
        original_dict = original.model_dump()
        recomputed_dict = recomputed.model_dump()
        
        differences = {}
        for key in original_dict.keys():
            if key in recomputed_dict:
                if original_dict[key] != recomputed_dict[key]:
                    if isinstance(original_dict[key], float) and isinstance(recomputed_dict[key], float):
                        # Check if floats are close
                        if abs(original_dict[key] - recomputed_dict[key]) < 0.0001:
                            continue
                    differences[key] = {
                        'original': original_dict[key],
                        'recomputed': recomputed_dict[key],
                        'difference': self._calculate_difference(original_dict[key], recomputed_dict[key])
                    }
        
        return {
            'identical': len(differences) == 0,
            'differences': differences,
            'decision_match': original_dict['decision']['label'] == recomputed_dict['decision']['label'],
            'confidence_diff': abs(original_dict['decision']['confidence'] - recomputed_dict['decision']['confidence'])
        }
    
    def _calculate_difference(self, original, recomputed):
        """Calculate difference between values"""
        if isinstance(original, (int, float)) and isinstance(recomputed, (int, float)):
            return abs(original - recomputed)
        return "type_mismatch"
    
    def batch_replay(self, event_ids: List[str] = None, 
                    recalculate: bool = True) -> Dict:
        """Batch replay multiple events"""
        if event_ids is None:
            # Get all event directories
            event_dirs = self.find_event_directories()
            event_ids = [d.name for d in event_dirs]
        
        results = {
            'total_events': len(event_ids),
            'successful_replays': 0,
            'failed_replays': 0,
            'events': []
        }
        
        for event_id in event_ids:
            try:
                result = self.replay_event(event_id, recalculate)
                results['events'].append({
                    'event_id': event_id,
                    'status': 'success',
                    'decision': result['convergence_metrics'].decision['label'],
                    'confidence': result['convergence_metrics'].decision['confidence'],
                    'deterministic_check': result.get('deterministic_check', 'N/A')
                })
                results['successful_replays'] += 1
            except Exception as e:
                results['events'].append({
                    'event_id': event_id,
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed_replays'] += 1
        
        return results
    
    def validate_artifact_contracts(self, event_id: str) -> Dict:
        """Validate that all required artifacts exist and are valid"""
        event_dir = self.artifacts_base_path / event_id
        if not event_dir.exists():
            return {'valid': False, 'error': f"Event directory not found: {event_id}"}
        
        validation_results = {
            'event_id': event_id,
            'valid': True,
            'missing_artifacts': [],
            'invalid_artifacts': [],
            'checks': {}
        }
        
        # Check 1: Incident text exists
        incident_path = event_dir / "incident.txt"
        validation_results['checks']['incident_text'] = incident_path.exists()
        if not incident_path.exists():
            validation_results['missing_artifacts'].append('incident.txt')
            validation_results['valid'] = False
        
        # Check 2: At least 2 evidence files per agent
        evidence_files = list(event_dir.glob("evidence_*.json"))
        validation_results['checks']['evidence_files'] = len(evidence_files) >= 2
        if len(evidence_files) < 2:
            validation_results['missing_artifacts'].append('evidence files (need at least 2)')
            validation_results['valid'] = False
        
        # Check 3: At least 2 claims files per agent
        claims_files = list(event_dir.glob("claims_*.json"))
        validation_results['checks']['claims_files'] = len(claims_files) >= 2
        if len(claims_files) < 2:
            validation_results['missing_artifacts'].append('claims files (need at least 2)')
            validation_results['valid'] = False
        
        # Check 4: Validate JSON schemas
        for evidence_file in evidence_files[:3]:  # Check up to 3
            try:
                with open(evidence_file, 'r') as f:
                    data = json.load(f)
                EvidenceExtraction(**data)
                validation_results['checks'][f'evidence_schema_{evidence_file.name}'] = True
            except Exception as e:
                validation_results['checks'][f'evidence_schema_{evidence_file.name}'] = False
                validation_results['invalid_artifacts'].append(str(evidence_file))
                validation_results['valid'] = False
        
        for claims_file in claims_files[:3]:
            try:
                with open(claims_file, 'r') as f:
                    data = json.load(f)
                AgentClaims(**data)
                validation_results['checks'][f'claims_schema_{claims_file.name}'] = True
            except Exception as e:
                validation_results['checks'][f'claims_schema_{claims_file.name}'] = False
                validation_results['invalid_artifacts'].append(str(claims_file))
                validation_results['valid'] = False
        
        # Check 5: Convergence metrics (optional but recommended)
        convergence_files = list(event_dir.glob("convergence_*.json"))
        validation_results['checks']['convergence_files'] = len(convergence_files) > 0
        if convergence_files:
            try:
                with open(convergence_files[0], 'r') as f:
                    data = json.load(f)
                ConvergenceMetrics(**data)
                validation_results['checks']['convergence_schema'] = True
            except Exception as e:
                validation_results['checks']['convergence_schema'] = False
                validation_results['invalid_artifacts'].append(str(convergence_files[0]))
        
        return validation_results
    
    def export_event_for_reproducibility(self, event_id: str, 
                                       output_path: Path) -> Path:
        """Export all event artifacts for reproducibility"""
        event_dir = self.artifacts_base_path / event_id
        if not event_dir.exists():
            raise ValueError(f"Event directory not found: {event_id}")
        
        # Create export directory
        export_dir = output_path / f"export_{event_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all artifacts
        import shutil
        for item in event_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, export_dir / item.name)
        
        # Create manifest
        manifest = {
            'event_id': event_id,
            'export_timestamp': datetime.utcnow().isoformat(),
            'system_version': '1.0.0',
            'convergence_engine_hash': self._get_convergence_engine_hash(),
            'artifacts': [item.name for item in export_dir.iterdir() if item.is_file()]
        }
        
        manifest_path = export_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create hash of all files
        total_hash = self._hash_directory(export_dir)
        manifest['directory_hash'] = total_hash
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return export_dir
    
    def _get_convergence_engine_hash(self) -> str:
        """Get hash of convergence engine code for reproducibility"""
        import inspect
        source = inspect.getsource(self.convergence_engine.compute_convergence)
        return hashlib.sha256(source.encode()).hexdigest()[:16]
    
    def _hash_directory(self, directory: Path) -> str:
        """Create hash of all files in directory"""
        hasher = hashlib.sha256()
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
        return hasher.hexdigest()