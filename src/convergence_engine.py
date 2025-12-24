# src/convergence_engine.py
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter
import math
from uuid import UUID

from src.schemas.evidence import EvidenceExtraction
from src.schemas.claims import AgentClaims, FinalLabel
from src.schemas.convergence import ConvergenceMetrics, AgentLabels
from src.config.settings import settings

class ConvergenceEngine:
    def __init__(self):
        self.consensus_threshold = settings.consensus_threshold
        self.jaccard_threshold = settings.jaccard_threshold
        self.residual_threshold = settings.residual_disagreement_threshold
        
    def compute_evidence_overlap(self, 
                                evidence_sets: Dict[str, set]) -> Dict[str, float]:
        """Compute Jaccard similarity between evidence sets"""
        agents = list(evidence_sets.keys())
        overlaps = {}
        
        # Pairwise Jaccard
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                key = f"{agents[i]}_{agents[j]}"
                set_a = evidence_sets[agents[i]]
                set_b = evidence_sets[agents[j]]
                
                if not set_a and not set_b:
                    jaccard = 1.0
                elif not set_a or not set_b:
                    jaccard = 0.0
                else:
                    intersection = len(set_a.intersection(set_b))
                    union = len(set_a.union(set_b))
                    jaccard = intersection / union if union > 0 else 0.0
                
                overlaps[key] = jaccard
        
        # Triple intersection
        if len(agents) == 3:
            triple_intersection = len(
                evidence_sets[agents[0]].intersection(
                    evidence_sets[agents[1]], 
                    evidence_sets[agents[2]]
                )
            )
            overlaps["triple_intersection_count"] = triple_intersection
        
        return overlaps
    
    def derive_agent_label(self, agent_claims: AgentClaims) -> FinalLabel:
        """Convert agent claims to a final label"""
        score = agent_claims.compute_label_score()
        
        if score >= self.consensus_threshold:
            return FinalLabel.MALICIOUS
        elif score <= -self.consensus_threshold:
            return FinalLabel.BENIGN
        else:
            return FinalLabel.UNCERTAIN
    
    def compute_disagreement_entropy(self, labels: Dict[str, FinalLabel]) -> float:
        """Compute normalized entropy of label distribution"""
        label_counts = Counter(labels.values())
        total = sum(label_counts.values())
        
        if total <= 1:
            return 0.0
            
        # Compute Shannon entropy
        entropy = 0.0
        for count in label_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # Normalize to [0, 1] (max entropy for 3 categories is log2(3) ≈ 1.585)
        max_entropy = math.log2(3)
        return entropy / max_entropy
    
    def compute_residual_disagreement(self,
                                     entropy: float,
                                     mean_overlap: float,
                                     conflict_flag: bool,
                                     mean_confidence: float) -> float:
        """Compute residual disagreement using specified formula"""
        # Formula: 0.55*entropy + 0.30*(1-overlap) + 0.15*(conflict*mean_confidence)
        conflict_term = 1.0 if conflict_flag else 0.0
        residual = (
            0.55 * entropy +
            0.30 * (1.0 - mean_overlap) +
            0.15 * (conflict_term * mean_confidence)
        )
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, residual))
    
    def compute_convergence(self,
                           evidence_extractions: Dict[str, EvidenceExtraction],
                           agent_claims: Dict[str, AgentClaims]) -> ConvergenceMetrics:
        """Main convergence computation - deterministic"""
        event_id = list(agent_claims.values())[0].event_id
        
        # 1. Compute evidence overlap
        evidence_sets = {
            agent_id: extraction.get_normalized_evidence_set()
            for agent_id, extraction in evidence_extractions.items()
        }
        
        evidence_overlap = self.compute_evidence_overlap(evidence_sets)
        mean_overlap = np.mean([
            v for k, v in evidence_overlap.items() 
            if not k.endswith("_count")
        ])
        
        # 2. Derive agent labels
        agent_labels = {
            agent_id: self.derive_agent_label(claims)
            for agent_id, claims in agent_claims.items()
        }
        
        # 3. Compute confidence alignment
        confidences = [claims.agent_confidence for claims in agent_claims.values()]
        mean_confidence = np.mean(confidences) if confidences else 0.0
        variance_confidence = np.var(confidences) if len(confidences) > 1 else 0.0
        
        # 4. Compute disagreement metrics
        entropy = self.compute_disagreement_entropy(agent_labels)
        
        # Check for label conflict
        unique_labels = set(agent_labels.values())
        conflict_flag = len(unique_labels) > 1
        
        # 5. Compute residual disagreement
        residual_disagreement = self.compute_residual_disagreement(
            entropy, mean_overlap, conflict_flag, mean_confidence
        )
        
        # 6. Make convergence decision
        decision, reason_codes = self._make_convergence_decision(
            agent_labels, mean_overlap, residual_disagreement, mean_confidence
        )
        
        return ConvergenceMetrics(
            event_id=event_id,
            agent_labels=AgentLabels(**agent_labels),
            evidence_intersection=evidence_overlap,
            disagreement_entropy=entropy,
            confidence_alignment={
                "mean_confidence": mean_confidence,
                "variance_confidence": variance_confidence
            },
            residual_disagreement=residual_disagreement,
            decision={
                "label": decision,
                "confidence": self._compute_decision_confidence(
                    decision, mean_confidence, residual_disagreement
                ),
                "reason_codes": reason_codes
            }
        )
    
    def _make_convergence_decision(self,
                                  agent_labels: Dict[str, FinalLabel],
                                  mean_overlap: float,
                                  residual_disagreement: float,
                                  mean_confidence: float) -> Tuple[FinalLabel, List[str]]:
        """Apply threshold logic to make final decision"""
        reason_codes = []
        
        # Check consensus conditions
        label_counts = Counter(agent_labels.values())
        
        # Condition 1: At least 2 of 3 agree on BENIGN/MALICIOUS
        benign_count = label_counts.get(FinalLabel.BENIGN, 0)
        malicious_count = label_counts.get(FinalLabel.MALICIOUS, 0)
        
        has_majority = (benign_count >= 2) or (malicious_count >= 2)
        
        if not has_majority:
            reason_codes.append("NO_MAJORITY_LABEL")
        
        # Condition 2: Residual disagreement threshold
        if residual_disagreement > self.residual_threshold:
            reason_codes.append("HIGH_RESIDUAL_DISAGREEMENT")
        
        # Condition 3: Evidence overlap threshold
        if mean_overlap < self.jaccard_threshold:
            reason_codes.append("LOW_EVIDENCE_OVERLAP")
        
        # Make decision
        if has_majority and residual_disagreement <= self.residual_threshold and mean_overlap >= self.jaccard_threshold:
            if benign_count >= 2:
                return FinalLabel.BENIGN, ["CONSENSUS_BENIGN"]
            else:
                return FinalLabel.MALICIOUS, ["CONSENSUS_MALICIOUS"]
        else:
            if len(reason_codes) == 0:
                reason_codes.append("AMBIGUOUS_EVIDENCE")
            return FinalLabel.UNCERTAIN, reason_codes
    
    def _compute_decision_confidence(self,
                                    decision: FinalLabel,
                                    mean_confidence: float,
                                    residual_disagreement: float) -> float:
        """Compute confidence for the final decision"""
        if decision == FinalLabel.UNCERTAIN:
            # Confidence in uncertainty
            return max(0.0, min(1.0, 1.0 - residual_disagreement))
        else:
            # Confidence in consensus decision
            confidence = mean_confidence * (1.0 - residual_disagreement)
            return max(0.0, min(1.0, confidence))