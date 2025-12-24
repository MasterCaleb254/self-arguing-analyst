# tests/test_agents.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from src.agents.benign_agent import BenignAgent
from src.agents.malicious_agent import MaliciousAgent
from src.agents.skeptic_agent import SkepticAgent

class TestAgents:
    def test_agent_initialization(self):
        """Test agent initialization"""
        benign = BenignAgent()
        assert benign.agent_id == "benign"
        assert "Benign Analyst" in benign.get_system_prompt_evidence()
        
        malicious = MaliciousAgent()
        assert malicious.agent_id == "malicious"
        assert "Malicious Analyst" in malicious.get_system_prompt_evidence()
        
        skeptic = SkepticAgent()
        assert skeptic.agent_id == "skeptic"
        assert "Skeptic Analyst" in skeptic.get_system_prompt_evidence()
    
    @patch('src.agents.base_agent.OpenAI')
    def test_evidence_extraction(self, mock_openai):
        """Test evidence extraction with mock"""
        # Mock the OpenAI response
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(
            content=json.dumps({
                "event_id": "test",
                "agent_id": "benign",
                "evidence": [
                    {
                        "evidence_id": "123",
                        "type": "domain",
                        "value": "example.com",
                        "source_spans": [
                            {
                                "start_char": 0,
                                "end_char": 11,
                                "quote": "example.com"
                            }
                        ],
                        "extraction_confidence": 0.9,
                        "notes": None
                    }
                ]
            })
        ))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client
        
        # Test extraction
        agent = BenignAgent()
        agent.client = mock_client
        
        evidence = agent.extract_evidence(
            event_id="test",
            incident_text="Visit to example.com detected"
        )
        
        assert evidence.agent_id == "benign"
        assert len(evidence.evidence) == 1
        assert evidence.evidence[0].value == "example.com"
        assert evidence.evidence[0].normalized["value"] == "example.com"
    
    def test_stance_contradiction(self):
        """Test that agents can contradict their stance"""
        # This is tested via the system prompts
        benign = BenignAgent()
        prompt = benign.get_system_prompt_claims()
        assert "contradict" in prompt.lower()
        
        malicious = MaliciousAgent()
        prompt = malicious.get_system_prompt_claims()
        assert "contradict" in prompt.lower()