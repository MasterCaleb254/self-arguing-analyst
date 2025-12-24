# src/schemas/claims.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from uuid import uuid4, UUID
from enum import Enum

class ClaimDirection(str, Enum):
    SUPPORTS_BENIGN = "supports_benign"
    SUPPORTS_MALICIOUS = "supports_malicious"
    NEUTRAL_OR_UNCLEAR = "neutral_or_unclear"

class Gap(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    gap: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)

class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    claim_id: UUID = Field(default_factory=uuid4)
    summary: str = Field(..., min_length=1)
    direction: ClaimDirection
    supporting_evidence_ids: List[UUID] = Field(default_factory=list)
    counter_evidence_ids: List[UUID] = Field(default_factory=list)
    claim_confidence: float = Field(..., ge=0.0, le=1.0)
    assumptions: List[str] = Field(default_factory=list)

class AgentStance(str, Enum):
    BENIGN_HYPOTHESIS = "BENIGN_HYPOTHESIS"
    MALICIOUS_HYPOTHESIS = "MALICIOUS_HYPOTHESIS"
    SKEPTICAL_HYPOTHESIS = "SKEPTICAL_HYPOTHESIS"

class AgentClaims(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    event_id: UUID
    agent_id: Literal["benign", "malicious", "skeptic"]
    stance: AgentStance
    claims: List[Claim] = Field(default_factory=list)
    agent_confidence: float = Field(..., ge=0.0, le=1.0)
    gaps: List[Gap] = Field(default_factory=list)
    
    def compute_label_score(self) -> float:
        """Compute weighted vote score for this agent's claims"""
        if not self.claims:
            return 0.0
            
        total_weight = 0.0
        weighted_sum = 0.0
        
        for claim in self.claims:
            weight = claim.claim_confidence
            if claim.direction == ClaimDirection.SUPPORTS_MALICIOUS:
                weighted_sum += weight * 1.0
            elif claim.direction == ClaimDirection.SUPPORTS_BENIGN:
                weighted_sum += weight * -1.0
            # Neutral doesn't add to sum
            total_weight += weight
            
        return weighted_sum / total_weight if total_weight > 0 else 0.0