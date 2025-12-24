# tests/test_replay.py
import pytest
import json
from pathlib import Path
import tempfile
import shutil

from src.replay.replay_engine import ArtifactReplayEngine
from src.schemas.evidence import EvidenceExtraction, EvidenceItem, SourceSpan, EvidenceType
from src.schemas.claims import AgentClaims, Claim, ClaimDirection, AgentStance
from src.schemas.convergence import ConvergenceMetrics, FinalLabel, AgentLabels

class TestArtifactReplayEngine:
    def setup_method(self):
        # Create temporary directory for artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.engine = ArtifactReplayEngine(Path(self.temp_dir))
    
    def teardown_method(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
    
    def create_test_event(self, event_id: str):
        """Create a test event with minimal artifacts"""
        event_dir = Path(self.temp_dir) / event_id
        event_dir.mkdir()
        
        # Create incident text
        incident_text = "Test incident with suspicious activity"
        (event_dir / "incident.txt").write_text(incident_text)
        
        # Create evidence artifacts
        evidence = EvidenceExtraction(
            event_id=event_id,
            agent_id="benign",
            evidence=[
                EvidenceItem(
                    type=EvidenceType.DOMAIN,
                    value="example.com",
                    source_spans=[SourceSpan(start_char=0, end_char=10, quote="example.com")],
                    extraction_confidence=0.9
                )
            ]
        )
        
        (event_dir / "evidence_benign_20240101T120000.json").write_text(
            evidence.model_dump_json(indent=2)
        )
        
        # Create claims artifacts
        claims = AgentClaims(
            event_id=event_id,
            agent_id="benign",
            stance=AgentStance.BENIGN_HYPOTHESIS,
            claims=[
                Claim(
                    summary="Test benign claim",
                    direction=ClaimDirection.SUPPORTS_BENIGN,
                    claim_confidence=0.7
                )
            ],
            agent_confidence=0.6
        )
        
        (event_dir / "claims_benign_20240101T120000.json").write_text(
            claims.model_dump_json(indent=2)
        )
        
        return event_dir
    
    def test_find_event_directories(self):
        """Test finding event directories"""
        # Create test events
        self.create_test_event("test-event-1")
        self.create_test_event("test-event-2")
        
        event_dirs = self.engine.find_event_directories()
        assert len(event_dirs) == 2
        assert any("test-event-1" in str(d) for d in event_dirs)
    
    def test_load_event_artifacts(self):
        """Test loading event artifacts"""
        event_id = "test-event-load"
        self.create_test_event(event_id)
        
        artifacts = self.engine.load_event_artifacts(Path(self.temp_dir) / event_id)
        
        assert artifacts is not None
        assert artifacts['event_id'] == event_id
        assert "Test incident" in artifacts['incident_text']
        assert 'benign' in artifacts['evidence_extractions']
        assert 'benign' in artifacts['agent_claims']
    
    def test_replay_event(self):
        """Test replaying an event"""
        event_id = "test-event-replay"
        event_dir = self.create_test_event(event_id)
        
        # Need at least 2 agents for convergence
        # Create second agent artifacts
        evidence2 = EvidenceExtraction(
            event_id=event_id,
            agent_id="malicious",
            evidence=[
                EvidenceItem(
                    type=EvidenceType.DOMAIN,
                    value="example.com",
                    source_spans=[SourceSpan(start_char=0, end_char=10, quote="example.com")],
                    extraction_confidence=0.9
                )
            ]
        )
        
        (event_dir / "evidence_malicious_20240101T120000.json").write_text(
            evidence2.model_dump_json(indent=2)
        )
        
        claims2 = AgentClaims(
            event_id=event_id,
            agent_id="malicious",
            stance=AgentStance.MALICIOUS_HYPOTHESIS,
            claims=[
                Claim(
                    summary="Test malicious claim",
                    direction=ClaimDirection.SUPPORTS_MALICIOUS,
                    claim_confidence=0.8
                )
            ],
            agent_confidence=0.7
        )
        
        (event_dir / "claims_malicious_20240101T120000.json").write_text(
            claims2.model_dump_json(indent=2)
        )
        
        # Replay event
        result = self.engine.replay_event(event_id)
        
        assert result['status'] in ['loaded_from_storage', 'recomputed']
        assert 'convergence_metrics' in result
        assert result['convergence_metrics'].event_id == event_id
    
    def test_validate_artifact_contracts(self):
        """Test artifact contract validation"""
        event_id = "test-event-validate"
        event_dir = self.create_test_event(event_id)
        
        # Initially should be invalid (only 1 agent)
        validation = self.engine.validate_artifact_contracts(event_id)
        assert not validation['valid']
        assert 'evidence files' in str(validation['missing_artifacts'])
        
        # Add second agent
        evidence2 = EvidenceExtraction(
            event_id=event_id,
            agent_id="malicious",
            evidence=[]
        )
        
        (event_dir / "evidence_malicious_20240101T120000.json").write_text(
            evidence2.model_dump_json(indent=2)
        )
        
        claims2 = AgentClaims(
            event_id=event_id,
            agent_id="malicious",
            stance=AgentStance.MALICIOUS_HYPOTHESIS,
            claims=[],
            agent_confidence=0.5
        )
        
        (event_dir / "claims_malicious_20240101T120000.json").write_text(
            claims2.model_dump_json(indent=2)
        )
        
        # Now should be valid
        validation = self.engine.validate_artifact_contracts(event_id)
        assert validation['valid']
    
    def test_deterministic_replay(self):
        """Test that replay is deterministic"""
        event_id = "test-event-deterministic"
        event_dir = self.create_test_event(event_id)
        
        # Create two identical agents
        for agent_id in ["benign", "malicious"]:
            evidence = EvidenceExtraction(
                event_id=event_id,
                agent_id=agent_id,
                evidence=[
                    EvidenceItem(
                        type=EvidenceType.DOMAIN,
                        value="example.com",
                        source_spans=[SourceSpan(start_char=0, end_char=10, quote="example.com")],
                        extraction_confidence=0.9
                    )
                ]
            )
            
            (event_dir / f"evidence_{agent_id}_20240101T120000.json").write_text(
                evidence.model_dump_json(indent=2)
            )
            
            claims = AgentClaims(
                event_id=event_id,
                agent_id=agent_id,
                stance=AgentStance.BENIGN_HYPOTHESIS if agent_id == "benign" else AgentStance.MALICIOUS_HYPOTHESIS,
                claims=[
                    Claim(
                        summary="Test claim",
                        direction=ClaimDirection.SUPPORTS_BENIGN if agent_id == "benign" else ClaimDirection.SUPPORTS_MALICIOUS,
                        claim_confidence=0.7
                    )
                ],
                agent_confidence=0.6
            )
            
            (event_dir / f"claims_{agent_id}_20240101T120000.json").write_text(
                claims.model_dump_json(indent=2)
            )
        
        # First replay
        result1 = self.engine.replay_event(event_id, recalculate=True)
        
        # Save convergence metrics
        convergence_file = event_dir / "convergence_test.json"
        with open(convergence_file, 'w') as f:
            f.write(result1['convergence_metrics'].model_dump_json(indent=2))
        
        # Second replay (should be identical)
        result2 = self.engine.replay_event(event_id, recalculate=True)
        
        # Compare
        assert result1['convergence_metrics'].decision['label'] == result2['convergence_metrics'].decision['label']
        assert abs(result1['convergence_metrics'].decision['confidence'] - 
                  result2['convergence_metrics'].decision['confidence']) < 0.0001
        
        # Test with existing convergence file
        result3 = self.engine.replay_event(event_id, recalculate=False)
        assert result3['status'] == 'loaded_from_storage'