# src/evaluation/harness.py
import json
import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
from sklearn.calibration import calibration_curve

from src.orchestrator import EventOrchestrator
from src.schemas.convergence import FinalLabel

@dataclass
class EvaluationResult:
    """Container for evaluation results"""
    incident_id: str
    ground_truth: Optional[str]  # BENIGN, MALICIOUS, or None for ambiguous
    system_label: FinalLabel
    system_confidence: float
    residual_disagreement: float
    is_correct: Optional[bool]  # None if ground_truth is None
    decision_reason_codes: List[str]
    agent_labels: Dict
    evidence_overlap: float
    processing_time: float

class EvaluationHarness:
    """Reproducible evaluation harness for labeled datasets"""
    
    def __init__(self, orchestrator: EventOrchestrator):
        self.orchestrator = orchestrator
        self.results: List[EvaluationResult] = []
        self.metrics: Dict = {}
    
    async def evaluate_dataset(self, dataset_path: Path, limit: Optional[int] = None) -> List[EvaluationResult]:
        """Evaluate on a labeled dataset"""
        incidents = self._load_dataset(dataset_path)
        
        if limit:
            incidents = incidents[:limit]
        
        print(f"[Evaluation] Starting evaluation on {len(incidents)} incidents...")
        
        for i, incident in enumerate(incidents, 1):
            print(f"[Evaluation] Processing incident {i}/{len(incidents)}: {incident['id']}")
            
            start_time = datetime.now()
            analysis_result = await self.orchestrator.analyze_incident(
                incident['text'],
                event_id=incident['id']
            )
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determine if correct (for non-ambiguous cases)
            is_correct = None
            if incident.get('ground_truth') and analysis_result['decision']['label'] != FinalLabel.UNCERTAIN:
                is_correct = (analysis_result['decision']['label'] == incident['ground_truth'])
            
            result = EvaluationResult(
                incident_id=incident['id'],
                ground_truth=incident.get('ground_truth'),
                system_label=analysis_result['decision']['label'],
                system_confidence=analysis_result['decision']['confidence'],
                residual_disagreement=analysis_result['summary']['residual_disagreement'],
                is_correct=is_correct,
                decision_reason_codes=analysis_result['decision']['reason_codes'],
                agent_labels=analysis_result['summary']['agent_labels'],
                evidence_overlap=np.mean(list(
                    analysis_result['summary']['evidence_overlap'].values()
                )),
                processing_time=processing_time
            )
            
            self.results.append(result)
        
        self._compute_metrics()
        return self.results
    
    def _load_dataset(self, dataset_path: Path) -> List[Dict]:
        """Load labeled dataset from JSONL format"""
        incidents = []
        
        with open(dataset_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    incidents.append({
                        'id': data.get('id', str(len(incidents))),
                        'text': data['text'],
                        'ground_truth': data.get('ground_truth')  # BENIGN, MALICIOUS, or None
                    })
        
        return incidents
    
    def _compute_metrics(self):
        """Compute comprehensive evaluation metrics"""
        if not self.results:
            return
        
        # Filter out incidents without ground truth for accuracy metrics
        labeled_results = [r for r in self.results if r.ground_truth is not None]
        ambiguous_results = [r for r in self.results if r.ground_truth is None]
        
        # Coverage metrics
        total_incidents = len(self.results)
        decided_incidents = [r for r in self.results if r.system_label != FinalLabel.UNCERTAIN]
        uncertain_incidents = [r for r in self.results if r.system_label == FinalLabel.UNCERTAIN]
        
        coverage = len(decided_incidents) / total_incidents if total_incidents > 0 else 0
        
        # Accuracy on confident outputs only
        correct_decisions = [r for r in decided_incidents if r.is_correct is True]
        accuracy = len(correct_decisions) / len(decided_incidents) if decided_incidents else 0
        
        # Justified Uncertainty Rate
        # UNCERTAIN outputs on ambiguous cases (should be high)
        ambiguous_uncertain = [r for r in ambiguous_results if r.system_label == FinalLabel.UNCERTAIN]
        justified_uncertainty_rate = len(ambiguous_uncertain) / len(ambiguous_results) if ambiguous_results else 0
        
        # Incorrect Uncertainty Rate
        # UNCERTAIN outputs on clear cases (should be low)
        clear_results = [r for r in labeled_results if r.ground_truth in [FinalLabel.BENIGN, FinalLabel.MALICIOUS]]
        clear_uncertain = [r for r in clear_results if r.system_label == FinalLabel.UNCERTAIN]
        incorrect_uncertainty_rate = len(clear_uncertain) / len(clear_results) if clear_results else 0
        
        # Calibration metrics
        if decided_incidents:
            confidences = [r.system_confidence for r in decided_incidents]
            corrects = [1 if r.is_correct else 0 for r in decided_incidents]
            
            # Expected Calibration Error (simplified)
            bins = np.linspace(0, 1, 11)
            bin_indices = np.digitize(confidences, bins) - 1
            ece = 0
            for i in range(len(bins) - 1):
                in_bin = np.where(bin_indices == i)[0]
                if len(in_bin) > 0:
                    bin_accuracy = np.mean([corrects[j] for j in in_bin])
                    bin_confidence = np.mean([confidences[j] for j in in_bin])
                    ece += (len(in_bin) / len(decided_incidents)) * abs(bin_accuracy - bin_confidence)
        else:
            ece = 0
        
        # Epistemic efficiency metrics
        avg_residual_disagreement = np.mean([r.residual_disagreement for r in self.results])
        avg_evidence_overlap = np.mean([r.evidence_overlap for r in self.results])
        avg_processing_time = np.mean([r.processing_time for r in self.results])
        
        self.metrics = {
            'total_incidents': total_incidents,
            'coverage': coverage,
            'accuracy': accuracy,
            'justified_uncertainty_rate': justified_uncertainty_rate,
            'incorrect_uncertainty_rate': incorrect_uncertainty_rate,
            'expected_calibration_error': ece,
            'avg_residual_disagreement': avg_residual_disagreement,
            'avg_evidence_overlap': avg_evidence_overlap,
            'avg_processing_time': avg_processing_time,
            'decided_count': len(decided_incidents),
            'uncertain_count': len(uncertain_incidents),
            'ambiguous_count': len(ambiguous_results),
            'clear_count': len(clear_results)
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive evaluation report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': self.metrics,
            'detailed_results': [
                {
                    'incident_id': r.incident_id,
                    'ground_truth': r.ground_truth,
                    'system_label': r.system_label,
                    'system_confidence': r.system_confidence,
                    'is_correct': r.is_correct,
                    'residual_disagreement': r.residual_disagreement,
                    'evidence_overlap': r.evidence_overlap,
                    'processing_time': r.processing_time
                }
                for r in self.results
            ]
        }
    
    def save_report(self, output_path: Path):
        """Save evaluation report to file"""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"[Evaluation] Report saved to {output_path}")