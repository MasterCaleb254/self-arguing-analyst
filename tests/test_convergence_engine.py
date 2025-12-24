# tests/test_convergence_engine.py
import pytest
import numpy as np
from src.convergence_engine import ConvergenceEngine
from src.schemas.evidence import EvidenceExtraction, EvidenceItem, SourceSpan, EvidenceType
from src.schemas.claims import AgentClaims, Claim, ClaimDirection, AgentStance
from src.schemas.convergence import FinalLabel

class TestConvergenceEngine:
    def setup_method(self):
        self.engine = ConvergenceEngine()
    
    def test_compute_evidence_overlap(self):
        """Test Jaccard similarity computation"""
        evidence_sets = {
            "benign": {"ip=192.168.1.1", "domain=example.com"},
            "malicious": {"ip=192.168.1.1", "domain=evil.com"},
            "skeptic": {"ip=192.168.1.1", "domain=example.com", "user=admin"}
        }
        
        overlaps = self.engine.compute_evidence_overlap(evidence_sets)
        
        # Check pairwise overlaps
        assert overlaps["benign_malicious"] == 1/3  # 1 common / 3 unique
        assert overlaps["benign_skeptic"] == 2/3    # 2 common / 3 unique
        assert overlaps["triple_intersection_count"] == 1  # Only IP matches all
    
    def test_derive_agent_label(self, sample_agent_claims):
        """Test agent label derivation from claims"""
        # Benign claim
        sample_agent_claims.claims = [
            Claim(
                summary="Benign activity",
                direction=ClaimDirection.SUPPORTS_BENIGN,
                claim_confidence=0.8
            )
        ]
        sample_agent_claims.agent_confidence = 0.7
        
        label = self.engine.derive_agent_label(sample_agent_claims)
        assert label == FinalLabel.BENIGN
        
        # Malicious claim
        sample_agent_claims.claims = [
            Claim(
                summary="Malicious activity",
                direction=ClaimDirection.SUPPORTS_MALICIOUS,
                claim_confidence=0.9
            )
        ]
        
        label = self.engine.derive_agent_label(sample_claims)
        assert label == FinalLabel.MALICIOUS
        
        # Neutral/ambiguous
        sample_agent_claims.claims = [
            Claim(
                summary="Unclear",
                direction=ClaimDirection.NEUTRAL_OR_UNCLEAR,
                claim_confidence=0.5
            )
        ]
        
        label = self.engine.derive_agent_label(sample_agent_claims)
        assert label == FinalLabel.UNCERTAIN
    
    def test_compute_disagreement_entropy(self):
        """Test disagreement entropy calculation"""
        # All agree
        labels = {
            "benign": FinalLabel.BENIGN,
            "malicious": FinalLabel.BENIGN,  # Changed stance!
            "skeptic": FinalLabel.BENIGN
        }
        entropy = self.engine.compute_disagreement_entropy(labels)
        assert entropy == 0.0  # No entropy when all agree
        
        # All disagree
        labels = {
            "benign": FinalLabel.BENIGN,
            "malicious": FinalLabel.MALICIOUS,
            "skeptic": FinalLabel.UNCERTAIN
        }
        entropy = self.engine.compute_disagreement_entropy(labels)
        assert 0.9 < entropy <= 1.0  # High entropy
    
    def test_compute_residual_disagreement(self):
        """Test residual disagreement calculation"""
        residual = self.engine.compute_residual_disagreement(
            entropy=0.8,
            mean_overlap=0.3,
            conflict_flag=True,
            mean_confidence=0.7
        )
        
        # Formula: 0.55*entropy + 0.30*(1-overlap) + 0.15*(conflict*mean_confidence)
        expected = 0.55*0.8 + 0.30*(1-0.3) + 0.15*(1*0.7)
        expected = max(0.0, min(1.0, expected))
        
        assert abs(residual - expected) < 0.001
    
    def test_make_convergence_decision(self):
        """Test convergence decision logic"""
        # Consensus case
        agent_labels = {
            "benign": FinalLabel.BENIGN,
            "malicious": FinalLabel.BENIGN,
            "skeptic": FinalLabel.UNCERTAIN
        }
        
        label, reasons = self.engine._make_convergence_decision(
            agent_labels=agent_labels,
            mean_overlap=0.5,
            residual_disagreement=0.2,
            mean_confidence=0.8
        )
        
        assert label == FinalLabel.BENIGN
        assert "CONSENSUS_BENIGN" in reasons
        
        # Uncertainty case
        agent_labels = {
            "benign": FinalLabel.BENIGN,
            "malicious": FinalLabel.MALICIOUS,
            "skeptic": FinalLabel.UNCERTAIN
        }
        
        label, reasons = self.engine._make_convergence_decision(
            agent_labels=agent_labels,
            mean_overlap=0.1,
            residual_disagreement=0.6,
            mean_confidence=0.5
        )
        
        assert label == FinalLabel.UNCERTAIN
        assert len(reasons) > 0