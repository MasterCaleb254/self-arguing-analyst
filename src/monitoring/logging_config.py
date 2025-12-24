# src/monitoring/logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import structlog
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure structured logging with structlog"""
    
    # Remove default handlers
    logging.getLogger().handlers.clear()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create logger
    logger = structlog.get_logger()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # JSON formatter for console
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # File handler (if specified)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10_485_760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    return logger

# Custom log processors for observability
class AnalysisLogger:
    """Logger with analysis-specific context"""
    
    def __init__(self, base_logger):
        self.logger = base_logger.bind(system="self-arguing-analyst")
    
    def analysis_start(self, event_id: str, incident_preview: str):
        """Log analysis start"""
        self.logger.info(
            "analysis_started",
            event_id=event_id,
            incident_preview=incident_preview[:100],
            timestamp=datetime.utcnow().isoformat()
        )
    
    def agent_start(self, event_id: str, agent_id: str, step: str):
        """Log agent processing start"""
        self.logger.info(
            "agent_processing_start",
            event_id=event_id,
            agent_id=agent_id,
            step=step,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def agent_complete(self, event_id: str, agent_id: str, step: str, 
                      evidence_count: int = None, claims_count: int = None):
        """Log agent processing completion"""
        self.logger.info(
            "agent_processing_complete",
            event_id=event_id,
            agent_id=agent_id,
            step=step,
            evidence_count=evidence_count,
            claims_count=claims_count,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def convergence_start(self, event_id: str):
        """Log convergence start"""
        self.logger.info(
            "convergence_start",
            event_id=event_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def decision_made(self, event_id: str, decision: str, confidence: float, 
                     residual_disagreement: float, reason_codes: list):
        """Log final decision"""
        self.logger.info(
            "decision_made",
            event_id=event_id,
            decision=decision,
            confidence=confidence,
            residual_disagreement=residual_disagreement,
            reason_codes=reason_codes,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def error(self, event_id: str, stage: str, error: Exception):
        """Log error"""
        self.logger.error(
            "analysis_error",
            event_id=event_id,
            stage=stage,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.utcnow().isoformat()
        )
    
    def epistemic_uncertainty(self, event_id: str, residual_disagreement: float, 
                             reasons: list):
        """Log epistemic uncertainty event"""
        self.logger.warning(
            "epistemic_uncertainty",
            event_id=event_id,
            residual_disagreement=residual_disagreement,
            reasons=reasons,
            timestamp=datetime.utcnow().isoformat()
        )