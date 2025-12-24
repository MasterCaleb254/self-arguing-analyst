# src/database/repository.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import Base, AnalysisEvent, AgentAnalysis, ConvergenceMetrics

class AnalysisRepository:
    """Repository for analysis data operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_event(self, incident_text: str, incident_hash: str) -> AnalysisEvent:
        """Create a new analysis event"""
        event = AnalysisEvent(
            incident_text=incident_text,
            incident_text_hash=incident_hash,
            submitted_at=datetime.utcnow(),
            status="pending"
        )
        
        self.session.add(event)
        self.session.flush()  # Get the ID without committing
        
        return event
    
    def update_event_status(self, event_id: str, status: str, 
                          final_label: Optional[str] = None,
                          final_confidence: Optional[float] = None,
                          residual_disagreement: Optional[float] = None):
        """Update event status and final results"""
        event = self.session.query(AnalysisEvent).filter_by(id=event_id).first()
        if event:
            event.status = status
            event.completed_at = datetime.utcnow() if status == "completed" else None
            event.final_label = final_label
            event.final_confidence = final_confidence
            event.residual_disagreement = residual_disagreement
    
    def add_agent_analysis(self, event_id: str, agent_id: str, role_name: str,
                         evidence_json: Dict, claims_json: Dict, 
                         agent_confidence: float, derived_label: str, label_score: float):
        """Add agent analysis results"""
        agent_analysis = AgentAnalysis(
            event_id=event_id,
            agent_id=agent_id,
            role_name=role_name,
            evidence_json=evidence_json,
            claims_json=claims_json,
            evidence_count=len(evidence_json.get("evidence", [])),
            claims_count=len(claims_json.get("claims", [])),
            agent_confidence=agent_confidence,
            derived_label=derived_label,
            label_score=label_score,
            completed_at=datetime.utcnow()
        )
        
        self.session.add(agent_analysis)
    
    def add_convergence_metrics(self, event_id: str, metrics: Dict):
        """Add convergence metrics"""
        convergence = ConvergenceMetrics(
            event_id=event_id,
            evidence_overlap_benign_malicious=metrics.get("benign_malicious", 0.0),
            evidence_overlap_benign_skeptic=metrics.get("benign_skeptic", 0.0),
            evidence_overlap_malicious_skeptic=metrics.get("malicious_skeptic", 0.0),
            triple_intersection_count=metrics.get("triple_intersection_count", 0),
            disagreement_entropy=metrics.get("disagreement_entropy", 0.0),
            mean_confidence=metrics.get("mean_confidence", 0.