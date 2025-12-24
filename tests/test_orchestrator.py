# tests/test_orchestrator.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.orchestrator import EventOrchestrator

class TestEventOrchestrator:
    @pytest.mark.asyncio
    async def test_parallel_evidence_extraction(self):
        """Test parallel evidence extraction"""
        orchestrator = EventOrchestrator(storage_path="./test_artifacts")
        
        # Mock agents
        mock_agent = Mock()
        mock_agent.extract_evidence.return_value = Mock(
            event_id="test",
            agent_id="benign",
            evidence=[],
            get_normalized_evidence_set=Mock(return_value=set())
        )
        
        orchestrator.agents = {
            "benign": mock_agent,
            "malicious": mock_agent,
            "skeptic": mock_agent
        }
        
        incident_text = "Test incident"
        evidence_extractions = await orchestrator._extract_evidence_parallel(
            event_id="test",
            incident_text=incident_text
        )
        
        assert len(evidence_extractions) == 3
        mock_agent.extract_evidence.assert_called()
    
    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, sample_incident_text):
        """Test complete analysis pipeline"""
        orchestrator = EventOrchestrator(storage_path="./test_artifacts")
        
        # Mock the entire process
        with patch.object(orchestrator, '_extract_evidence_parallel') as mock_extract, \
             patch.object(orchestrator, '_generate_claims_parallel') as mock_claims, \
             patch.object(orchestrator.convergence_engine, 'compute_convergence') as mock_converge:
            
            # Setup mocks
            mock_extract.return_value = {
                "benign": Mock(get_normalized_evidence_set=Mock(return_value=set())),
                "malicious": Mock(get_normalized_evidence_set=Mock(return_value=set())),
                "skeptic": Mock(get_normalized_evidence_set=Mock(return_value=set()))
            }
            
            mock_claims.return_value = {
                "benign": Mock(
                    event_id="test",
                    agent_id="benign",
                    compute_label_score=Mock(return_value=-0.5),
                    agent_confidence=0.7
                ),
                "malicious": Mock(
                    event_id="test",
                    agent_id="malicious",
                    compute_label_score=Mock(return_value=0.3),
                    agent_confidence=0.8
                ),
                "skeptic": Mock(
                    event_id="test",
                    agent_id="skeptic",
                    compute_label_score=Mock(return_value=0.0),
                    agent_confidence=0.5
                )
            }
            
            mock_converge.return_value = Mock(
                event_id="test",
                agent_labels=Mock(benign="BENIGN", malicious="MALICIOUS", skeptic="UNCERTAIN"),
                decision={"label": "UNCERTAIN", "confidence": 0.6, "reason_codes": ["NO_MAJORITY"]}
            )
            
            # Run analysis
            result = await orchestrator.analyze_incident(sample_incident_text)
            
            assert "decision" in result
            assert "epistemic_status" in result
            assert result["decision"]["label"] == "UNCERTAIN"
    
    def test_artifact_persistence(self, tmp_path):
        """Test artifact persistence to disk"""
        orchestrator = EventOrchestrator(storage_path=str(tmp_path))
        
        # Mock data
        evidence_extractions = {
            "benign": Mock(
                event_id="test",
                agent_id="benign",
                evidence=[],
                model_dump_json=Mock(return_value="{}")
            )
        }
        
        agent_claims = {
            "benign": Mock(
                event_id="test",
                agent_id="benign",
                model_dump_json=Mock(return_value="{}")
            )
        }
        
        convergence_metrics = Mock(
            event_id="test",
            model_dump_json=Mock(return_value="{}")
        )
        
        # Test persistence
        orchestrator._persist_artifacts(
            event_id="test",
            incident_text="test",
            evidence_extractions=evidence_extractions,
            agent_claims=agent_claims,
            convergence_metrics=convergence_metrics
        )
        
        # Check files were created
        event_dir = tmp_path / "test"
        assert event_dir.exists()
        assert (event_dir / "incident.txt").exists()
        assert len(list(event_dir.glob("evidence_*.json"))) > 0
        assert len(list(event_dir.glob("claims_*.json"))) > 0
        assert len(list(event_dir.glob("convergence_*.json"))) > 0