# src/monitoring/metrics.py
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest
from prometheus_client.registry import CollectorRegistry
import time
from typing import Dict, Any

class MetricsCollector:
    """Metrics collector for system observability"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Analysis metrics
        self.analysis_requests = Counter(
            'analysis_requests_total',
            'Total analysis requests',
            ['priority', 'status'],
            registry=self.registry
        )
        
        self.analysis_duration = Histogram(
            'analysis_duration_seconds',
            'Analysis processing time',
            ['result'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
            registry=self.registry
        )
        
        # Agent metrics
        self.agent_calls = Counter(
            'agent_calls_total',
            'Total agent LLM calls',
            ['agent_type', 'step'],
            registry=self.registry
        )
        
        self.agent_errors = Counter(
            'agent_errors_total',
            'Agent processing errors',
            ['agent_type', 'error_type'],
            registry=self.registry
        )
        
        # Decision metrics
        self.decisions = Counter(
            'decisions_total',
            'Final decisions by type',
            ['decision_type'],
            registry=self.registry
        )
        
        self.residual_disagreement = Gauge(
            'residual_disagreement',
            'Current residual disagreement',
            registry=self.registry
        )
        
        self.uncertainty_rate = Gauge(
            'uncertainty_rate',
            'Rate of UNCERTAIN decisions',
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'analysis_queue_size',
            'Current analysis queue size',
            registry=self.registry
        )
        
        self.processing_time = Summary(
            'processing_time_seconds',
            'Analysis processing time summary',
            registry=self.registry
        )
    
    def record_analysis_start(self, priority: str = "normal"):
        """Record analysis request start"""
        self.analysis_requests.labels(priority=priority, status="started").inc()
    
    def record_analysis_complete(self, duration: float, result: str):
        """Record analysis completion"""
        self.analysis_duration.labels(result=result).observe(duration)
        self.analysis_requests.labels(priority="normal", status="completed").inc()
    
    def record_agent_call(self, agent_type: str, step: str):
        """Record agent LLM call"""
        self.agent_calls.labels(agent_type=agent_type, step=step).inc()
    
    def record_agent_error(self, agent_type: str, error_type: str):
        """Record agent error"""
        self.agent_errors.labels(agent_type=agent_type, error_type=error_type).inc()
    
    def record_decision(self, decision_type: str):
        """Record final decision"""
        self.decisions.labels(decision_type=decision_type).inc()
    
    def update_residual_disagreement(self, value: float):
        """Update residual disagreement gauge"""
        self.residual_disagreement.set(value)
    
    def update_uncertainty_rate(self, rate: float):
        """Update uncertainty rate gauge"""
        self.uncertainty_rate.set(rate)
    
    def update_queue_size(self, size: int):
        """Update queue size gauge"""
        self.queue_size.set(size)
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)

# Global metrics collector
metrics = MetricsCollector()