# src/database/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class AnalysisEvent(Base):
    """Analysis event table"""
    __tablename__ = "analysis_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    incident_text = Column(String, nullable=False)
    incident_text_hash = Column(String, nullable=False, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Final decision
    final_label = Column(String, nullable=True)  # BENIGN, MALICIOUS, UNCERTAIN
    final_confidence = Column(Float, nullable=True)
    residual_disagreement = Column(Float, nullable=True)
    
    # Relationships
    agents = relationship("AgentAnalysis", back_populates="event", cascade="all, delete-orphan")
    convergence_metrics = relationship("ConvergenceMetrics", back_populates="event", uselist=False)

class AgentAnalysis(Base):
    """Per-agent analysis results"""
    __tablename__ = "agent_analyses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("analysis_events.id"), nullable=False)
    agent_id = Column(String, nullable=False)  # benign, malicious, skeptic
    role_name = Column(String, nullable=False)
    
    # Evidence extraction
    evidence_count = Column(Integer, default=0)
    evidence_json = Column(JSON, nullable=True)
    
    # Claims
    claims_count = Column(Integer, default=0)
    agent_confidence = Column(Float, nullable=True)
    derived_label = Column(String, nullable=True)  # BENIGN, MALICIOUS, UNCERTAIN
    label_score = Column(Float, nullable=True)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    event = relationship("AnalysisEvent", back_populates="agents")

class ConvergenceMetrics(Base):
    """Convergence metrics storage"""
    __tablename__ = "convergence_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("analysis_events.id"), nullable=False, unique=True)
    
    # Evidence overlap
    evidence_overlap_benign_malicious = Column(Float, nullable=True)
    evidence_overlap_benign_skeptic = Column(Float, nullable=True)
    evidence_overlap_malicious_skeptic = Column(Float, nullable=True)
    triple_intersection_count = Column(Integer, nullable=True)
    
    # Disagreement metrics
    disagreement_entropy = Column(Float, nullable=True)
    mean_confidence = Column(Float, nullable=True)
    confidence_variance = Column(Float, nullable=True)
    residual_disagreement = Column(Float, nullable=True)
    
    # Decision
    decision_label = Column(String, nullable=True)
    decision_confidence = Column(Float, nullable=True)
    reason_codes = Column(JSON, nullable=True)  # List of strings
    
    # Relationships
    event = relationship("AnalysisEvent", back_populates="convergence_metrics")

class EvaluationResult(Base):
    """Evaluation results for research"""
    __tablename__ = "evaluation_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_name = Column(String, nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Metrics
    total_incidents = Column(Integer, nullable=False)
    coverage = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    justified_uncertainty_rate = Column(Float, nullable=True)
    incorrect_uncertainty_rate = Column(Float, nullable=True)
    expected_calibration_error = Column(Float, nullable=True)
    avg_residual_disagreement = Column(Float, nullable=True)
    
    # Configuration
    configuration_json = Column(JSON, nullable=False)
    
    # Relationships
    incident_results = relationship("EvaluationIncidentResult", back_populates="evaluation")

class EvaluationIncidentResult(Base):
    """Individual incident results within an evaluation"""
    __tablename__ = "evaluation_incident_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evaluation_id = Column(String, ForeignKey("evaluation_results.id"), nullable=False)
    incident_id = Column(String, nullable=False)
    
    # Ground truth
    ground_truth = Column(String, nullable=True)  # BENIGN, MALICIOUS, None
    
    # System output
    system_label = Column(String, nullable=False)
    system_confidence = Column(Float, nullable=False)
    residual_disagreement = Column(Float, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    
    # Agent-level
    agent_labels_json = Column(JSON, nullable=False)  # {agent: label}
    evidence_overlap = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    
    # Relationships
    evaluation = relationship("EvaluationResult", back_populates="incident_results")