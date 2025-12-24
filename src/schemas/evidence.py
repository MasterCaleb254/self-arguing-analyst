# src/schemas/evidence.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from uuid import uuid4, UUID
from enum import Enum

class EvidenceType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    FILE_PATH = "file_path"
    PROCESS = "process"
    COMMAND_LINE = "command_line"
    REGISTRY = "registry"
    USER = "user"
    HOST = "host"
    TIMESTAMP = "timestamp"
    NETWORK_FLOW = "network_flow"
    EMAIL = "email"
    BEHAVIOR = "behavior"
    ALERT = "alert"
    POLICY = "policy"
    OTHER = "other"

class SourceSpan(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., gt=0)
    quote: str = Field(..., min_length=1)

class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    evidence_id: UUID = Field(default_factory=uuid4)
    type: EvidenceType
    value: str = Field(..., min_length=1)
    normalized: dict[str, str] = Field(
        default_factory=lambda: {"key": "", "value": ""}
    )
    source_spans: List[SourceSpan] = Field(..., min_length=1)
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None

class EvidenceExtraction(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    event_id: UUID
    agent_id: Literal["benign", "malicious", "skeptic"]
    artifact_version: str = "1.0.0"
    evidence: List[EvidenceItem] = Field(default_factory=list)
    
    def get_normalized_evidence_set(self) -> set[str]:
        """Return normalized evidence for overlap computation"""
        evidence_set = set()
        for item in self.evidence:
            if item.normalized.get("key") and item.normalized.get("value"):
                key = item.normalized["key"]
                value = item.normalized["value"]
                evidence_set.add(f"{key}={value}")
        return evidence_set