# tests/conftest.py
import pytest
import asyncio
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock, patch
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.schemas.evidence import EvidenceExtraction, EvidenceItem, SourceSpan, EvidenceType
from src.schemas.claims import AgentClaims, Claim, ClaimDirection, AgentStance
from src.schemas.convergence import ConvergenceMetrics, FinalLabel, AgentLabels

@pytest.fixture
def sample_incident_text():
    return """At 14:30 UTC, user jsmith@company.com downloaded a file from suspicious-domain.com. 
    File hash: a1b2c3d4e5f6789012345678901234567890abcde. 
    The file was executed and created registry key HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater.
    Network traffic detected to 192.168.1.100 on port 443. 
    No antivirus alerts triggered."""

@pytest.fixture
def sample_evidence_extraction():
    return EvidenceExtraction(
        event_id="123e4567-e89b-12d3-a456-426614174000",
        agent_id="benign",
        evidence=[
            EvidenceItem(
                type=EvidenceType.DOMAIN,
                value="suspicious-domain.com",
                source_spans=[SourceSpan(start_char=50, end_char=72, quote="suspicious-domain.com")],
                extraction_confidence=0.9
            ),
            EvidenceItem(
                type=EvidenceType.FILE_HASH,
                value="a1b2c3d4e5f6789012345678901234567890abcde",
                source_spans=[SourceSpan(start_char=85, end_char=125, quote="a1b2c3d4e5f6789012345678901234567890abcde")],
                extraction_confidence=0.95
            )
        ]
    )

@pytest.fixture
def sample_agent_claims():
    return AgentClaims(
        event_id="123e4567-e89b-12d3-a456-426614174000",
        agent_id="benign",
        stance=AgentStance.BENIGN_HYPOTHESIS,
        claims=[
            Claim(
                summary="File download appears to be legitimate software update",
                direction=ClaimDirection.SUPPORTS_BENIGN,
                claim_confidence=0.7
            )
        ],
        agent_confidence=0.65
    )

@pytest.fixture
def mock_openai_response():
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "event_id": "123e4567-e89b-12d3-a456-426614174000",
                        "agent_id": "benign",
                        "evidence": [
                            {
                                "evidence_id": "456e4567-e89b-12d3-a456-426614174000",
                                "type": "domain",
                                "value": "example.com",
                                "source_spans": [
                                    {
                                        "start_char": 0,
                                        "end_char": 10,
                                        "quote": "example.com"
                                    }
                                ],
                                "extraction_confidence": 0.9,
                                "notes": "test"
                            }
                        ]
                    })
                }
            }
        ]
    }

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()