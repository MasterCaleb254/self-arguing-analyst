# src/schemas/convergence.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from uuid import UUID
from enum import Enum

class FinalLabel(str, Enum):
    BENIGN = "BENIGN"
    MALICIOUS = "MALICIOUS"
    UNCERTAIN = "UNCERTAIN"

class AgentLabels(BaseModel):
    benign: FinalLabel
    malicious: FinalLabel
    skeptic: FinalLabel

class ConvergenceMetrics(BaseModel):
    event_id: UUID
    agent_labels: AgentLabels
    evidence_intersection: Dict[str, float] = Field(
        default_factory=lambda: {
            "benign_malicious": 0.0,
            "benign_skeptic": 0.0,
            "malicious_skeptic": 0.0,
            "triple_intersection_count": 0
        }
    )
    disagreement_entropy: float = Field(..., ge=0.0, le=1.0)
    confidence_alignment: Dict[str, float] = Field(
        default_factory=lambda: {
            "mean_confidence": 0.0,
            "variance_confidence": 0.0
        }
    )
    residual_disagreement: float = Field(..., ge=0.0, le=1.0)
    decision: Dict[str, any] = Field(
        default_factory=lambda: {
            "label": FinalLabel.UNCERTAIN,
            "confidence": 0.0,
            "reason_codes": []
        }
    )