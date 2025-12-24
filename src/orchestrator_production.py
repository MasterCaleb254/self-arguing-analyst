# src/orchestrator_production.py
import asyncio
import json
import hashlib
from typing import Dict, Optional
from uuid import uuid4, UUID
from datetime import datetime
import os

from src.orchestrator_enhanced import EnhancedOrchestrator
from src.database.repository import AnalysisRepository
from src.database.session import db_manager
from src.monitoring.metrics import metrics
from src.monitoring.logging_config import AnalysisLogger, setup_logging

class ProductionOrchestrator(EnhancedOrchestrator):
    """Production-ready orchestrator with monitoring and database"""
    
    def __init__(self, config=None, storage_path=None):
        super().__init__(config, storage_path)
        
        # Setup logging
        self.logger = AnalysisLogger(
            setup_logging(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE")
            )
        )
        
        # Database session
        self.db_session = db_manager.get_session_direct()
        self.repository = AnalysisRepository(self.db_session)
    
    async def analyze_incident(self, incident_text: str, 
                              event_id: Optional[UUID] = None) -> Dict:
        """Production analysis with monitoring and database"""
        
        # Generate event ID if not provided
        if not event_id:
            event_id = uuid4()
        
        # Create hash for deduplication
        incident_hash = hashlib.sha256(incident_text.encode()).hexdigest()
        
        # Record metrics
        metrics.record_analysis_start()
        start_time = datetime.utcnow()
        
        try:
            # Log analysis start
            self.logger.analysis_start(
                event_id=str(event_id),
                incident_preview=incident_text[:100]
            )
            
            # Create database record
            event = self.repository.create_event(incident_text, incident_hash)
            self.db_session.commit()
            
            # Run analysis
            result = await super().analyze_incident_enhanced(incident_text, event_id)
            
            # Update database with results
            self._save_to_database(event.id, result)
            
            # Record success metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics.record_analysis_complete(duration, "success")
            metrics.record_decision(result['decision']['label'])
            metrics.update_residual_disagreement(result['summary']['residual_disagreement'])
            
            # Log decision
            self.logger.decision_made(
                event_id=str(event_id),
                decision=result['decision']['label'],
                confidence=result['decision']['confidence'],
                residual_disagreement=result['summary']['residual_disagreement'],
                reason_codes=result['decision']['reason_codes']
            )
            
            # Add database ID to result
            result['database_id'] = event.id
            
            return result
            
        except Exception as e:
            # Record error metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics.record_analysis_complete(duration, "error")
            
            # Log error
            self.logger.error(
                event_id=str(event_id),
                stage="analysis",
                error=e
            )
            
            # Update database
            if 'event' in locals():
                self.repository.update_event_status(event.id, "failed")
                self.db_session.commit()
            
            raise
    
    def _save_to_database(self, event_id: str, analysis_result: Dict):
        """Save analysis results to database"""
        try:
            # Load artifacts from disk
            artifacts_dir = os.path.join(
                self.storage_path,
                str(analysis_result['event_id'])
            )
            
            # Save agent analyses
            for agent_id in ["benign", "malicious", "skeptic"]:
                evidence_file = os.path.join(artifacts_dir, f"evidence_{agent_id}_*.json")
                claims_file = os.path.join(artifacts_dir, f"claims_{agent_id}_*.json")
                
                if os.path.exists(evidence_file) and os.path.exists(claims_file):
                    with open(evidence_file, 'r') as f:
                        evidence_json = json.load(f)
                    
                    with open(claims_file, 'r') as f:
                        claims_json = json.load(f)
                    
                    # Get agent label
                    agent_info = analysis_result['summary']['agent_labels'][agent_id]
                    
                    self.repository.add_agent_analysis(
                        event_id=event_id,
                        agent_id=agent_id,
                        role_name=agent_id,
                        evidence_json=evidence_json,
                        claims_json=claims_json,
                        agent_confidence=agent_info['confidence'],
                        derived_label=agent_info['label'],
                        label_score=agent_info['label_score']
                    )
            
            # Save convergence metrics
            convergence_metrics = {
                "benign_malicious": analysis_result['summary']['evidence_overlap'].get('benign_malicious', 0.0),
                "benign_skeptic": analysis_result['summary']['evidence_overlap'].get('benign_skeptic', 0.0),
                "malicious_skeptic": analysis_result['summary']['evidence_overlap'].get('malicious_skeptic', 0.0),
                "triple_intersection_count": analysis_result['summary']['evidence_overlap'].get('triple_intersection_count', 0),
                "disagreement_entropy": analysis_result['summary']['disagreement_entropy'],
                "mean_confidence": analysis_result['summary']['agent_labels'].values().agent_confidence.mean(),
                "variance_confidence": analysis_result['summary']['agent_labels'].values().agent_confidence.var(),
                "residual_disagreement": analysis_result['summary']['residual_disagreement'],
                "decision_label": analysis_result['decision']['label'],
                "decision_confidence": analysis_result['decision']['confidence'],
                "reason_codes": analysis_result['decision']['reason_codes']
            }
            
            self.repository.add_convergence_metrics(event_id, convergence_metrics)
            
            # Update event status
            self.repository.update_event_status(
                event_id=event_id,
                status="completed",
                final_label=analysis_result['decision']['label'],
                final_confidence=analysis_result['decision']['confidence'],
                residual_disagreement=analysis_result['summary']['residual_disagreement']
            )
            
            self.db_session.commit()
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(
                event_id=event_id,
                stage="database_save",
                error=e
            )
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Get system statistics from database"""
        return self.repository.get_statistics(days)
    
    def cleanup_old_artifacts(self, days_old: int = 7):
        """Clean up old artifacts from disk"""
        import shutil
        from pathlib import Path
        
        artifacts_dir = Path(self.storage_path)
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        for event_dir in artifacts_dir.iterdir():
            if event_dir.is_dir():
                try:
                    # Check if directory is old
                    if event_dir.stat().st_mtime < cutoff_time:
                        shutil.rmtree(event_dir)
                        self.logger.info(
                            "artifact_cleaned",
                            event_dir=str(event_dir),
                            timestamp=datetime.utcnow().isoformat()
                        )
                except Exception as e:
                    self.logger.error(
                        "cleanup_error",
                        event_dir=str(event_dir),
                        error=str(e)
                    )