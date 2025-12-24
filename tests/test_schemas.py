# tests/test_schemas.py
import pytest
from uuid import UUID
from src.schemas.evidence import EvidenceExtraction, EvidenceItem, SourceSpan, EvidenceType
from src.schemas.claims import AgentClaims, Claim, ClaimDirection, AgentStance
from src.schemas.convergence import ConvergenceMetrics, FinalLabel, AgentLabels

class TestEvidenceSchemas:
    def test_evidence_item_normalization(self):
        """Test evidence item normalization"""
        item = EvidenceItem(
            type=EvidenceType.DOMAIN,
            value="EXAMPLE.COM",
            source_spans=[SourceSpan(start_char=0, end_char=10, quote="EXAMPLE.COM")],
            extraction_confidence=0.9
        )
        
        assert item.normalized["key"] == "domain"
        assert item.normalized["value"] == "example.com"
    
    def test_evidence_extraction_get_normalized_set(self, sample_evidence_extraction):
        """Test evidence set extraction"""
        evidence_set = sample_evidence_extraction.get_normalized_evidence_set()
        assert len(evidence_set) == 2
        assert "domain=suspicious-domain.com" in evidence_set
    
    def test_evidence_item_validation(self):
        """Test evidence item validation constraints"""
        # Invalid confidence
        with pytest.raises(ValueError):
            EvidenceItem(
                type=EvidenceType.DOMAIN,
                value="test.com",
                source_spans=[SourceSpan(start_char=0, end_char=7, quote="test.com")],
                extraction_confidence=1.5  # Should be <= 1.0
            )
        
        # Empty source spans
        with pytest.raises(ValueError):
            EvidenceItem(
                type=EvidenceType.DOMAIN,
                value="test.com",
                source_spans=[],
                extraction_confidence=0.9
            )

class TestClaimsSchemas:
    def test_agent_claims_label_score(self, sample_agent_claims):
        """Test label score computation"""
        score = sample_agent_claims.compute_label_score()
        assert score == -0.7  # Supports benign is negative
        
        # Add malicious claim
        malicious_claim = Claim(
            summary="This looks malicious",
            direction=ClaimDirection.SUPPORTS_MALICIOUS,
            claim_confidence=0.8
        )
        sample_agent_claims.claims.append(malicious_claim)
        
        # New score should be weighted average
        score = sample_agent_claims.compute_label_score()
        expected = (-0.7 + 0.8) / (0.7 + 0.8)
        assert abs(score - expected) < 0.01
    
    def test_claim_direction_enum(self):
        """Test claim direction enum values"""
        assert ClaimDirection.SUPPORTS_BENIGN.value == "supports_benign"
        assert ClaimDirection.SUPPORTS_MALICIOUS.value == "supports_malicious"
        assert ClaimDirection.NEUTRAL_OR_UNCLEAR.value == "neutral_or_unclear"

class TestConvergenceSchemas:
    def test_agent_labels_validation(self):
        """Test agent labels validation"""
        labels = AgentLabels(
            benign=FinalLabel.BENIGN,
            malicious=FinalLabel.MALICIOUS,
            skeptic=FinalLabel.UNCERTAIN
        )
        
        assert isinstance(labels.benign, FinalLabel)
        assert labels.benign == FinalLabel.BENIGN