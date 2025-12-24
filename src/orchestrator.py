# src/orchestrator.py
import asyncio
import json
from typing import Dict, Optional
from uuid import uuid4, UUID
from datetime import datetime
import os

from src.agents.benign_agent import BenignAgent
from src.agents.malicious_agent import MaliciousAgent
from src.agents.skeptic_agent import SkepticAgent
from src.convergence_engine import ConvergenceEngine
from src.schemas.evidence import EvidenceExtraction
from src.schemas.claims import AgentClaims
from src.schemas.convergence import ConvergenceMetrics
from src.config.settings import settings

class EventOrchestrator:
    def __init__(self, storage_path: Optional[str] = None):
        self.agents = {
            "benign": BenignAgent(),
            "malicious": MaliciousAgent(),
            "skeptic": SkepticAgent()
        }
        self.convergence_engine = ConvergenceEngine()
        self.storage_path = storage_path or settings.artifact_storage_path
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def analyze_incident(self, incident_text: str, 
                              event_id: Optional[UUID] = None) -> Dict:
        """Main analysis pipeline"""
        # Generate event ID if not provided
        if not event_id:
            event_id = uuid4()
        
        print(f"[Orchestrator] Starting analysis for event: {event_id}")
        
        # Step 1: Parallel evidence extraction
        print(f"[Orchestrator] Extracting evidence in parallel...")
        evidence_extractions = await self._extract_evidence_parallel(
            event_id, incident_text
        )
        
        # Step 2: Parallel claims generation
        print(f"[Orchestrator] Generating claims in parallel...")
        agent_claims = await self._generate_claims_parallel(
            event_id, incident_text, evidence_extractions
        )
        
        # Step 3: Compute convergence
        print(f"[Orchestrator] Computing convergence metrics...")
        convergence_metrics = self.convergence_engine.compute_convergence(
            evidence_extractions, agent_claims
        )
        
        # Step 4: Persist artifacts
        print(f"[Orchestrator] Persisting artifacts...")
        self._persist_artifacts(
            event_id, incident_text, 
            evidence_extractions, agent_claims, convergence_metrics
        )
        
        # Step 5: Prepare final output
        final_output = self._prepare_final_output(
            incident_text, convergence_metrics, 
            evidence_extractions, agent_claims
        )
        
        print(f"[Orchestrator] Analysis complete. Decision: {final_output['decision']['label']}")
        
        return final_output
    
    async def _extract_evidence_parallel(self, event_id: UUID, incident_text: str) -> Dict[str, EvidenceExtraction]:
        """Run evidence extraction for all agents in parallel"""
        tasks = []
        for agent_id, agent in self.agents.items():
            # Run each agent in its own thread (I/O bound)
            task = asyncio.to_thread(
                agent.extract_evidence,
                str(event_id),
                incident_text
            )
            tasks.append((agent_id, task))
        
        # Execute in parallel
        results = {}
        for agent_id, task in tasks:
            try:
                results[agent_id] = await task
            except Exception as e:
                print(f"[Orchestrator] Error in {agent_id} evidence extraction: {e}")
                # Create empty evidence extraction on error
                results[agent_id] = EvidenceExtraction(
                    event_id=event_id,
                    agent_id=agent_id,
                    evidence=[]
                )
        
        return results
    
    async def _generate_claims_parallel(self, event_id: UUID, incident_text: str,
                                      evidence_extractions: Dict[str, EvidenceExtraction]) -> Dict[str, AgentClaims]:
        """Run claims generation for all agents in parallel"""
        tasks = []
        for agent_id, agent in self.agents.items():
            evidence = evidence_extractions.get(agent_id)
            if not evidence:
                continue
                
            task = asyncio.to_thread(
                agent.generate_claims,
                str(event_id),
                incident_text,
                evidence
            )
            tasks.append((agent_id, task))
        
        # Execute in parallel
        results = {}
        for agent_id, task in tasks:
            try:
                results[agent_id] = await task
            except Exception as e:
                print(f"[Orchestrator] Error in {agent_id} claims generation: {e}")
                # Create default claims on error
                results[agent_id] = AgentClaims(
                    event_id=event_id,
                    agent_id=agent_id,
                    stance="SKEPTICAL_HYPOTHESIS" if agent_id == "skeptic" else 
                           "BENIGN_HYPOTHESIS" if agent_id == "benign" else 
                           "MALICIOUS_HYPOTHESIS",
                    claims=[],
                    agent_confidence=0.0,
                    gaps=[]
                )
        
        return results
    
    def _persist_artifacts(self, event_id: UUID, incident_text: str,
                          evidence_extractions: Dict[str, EvidenceExtraction],
                          agent_claims: Dict[str, AgentClaims],
                          convergence_metrics: ConvergenceMetrics):
        """Save all artifacts to disk"""
        timestamp = datetime.utcnow().isoformat()
        event_dir = os.path.join(self.storage_path, str(event_id))
        os.makedirs(event_dir, exist_ok=True)
        
        # Save raw incident text
        with open(os.path.join(event_dir, "incident.txt"), "w") as f:
            f.write(incident_text)
        
        # Save evidence extractions
        for agent_id, extraction in evidence_extractions.items():
            filename = f"evidence_{agent_id}_{timestamp}.json"
            with open(os.path.join(event_dir, filename), "w") as f:
                f.write(extraction.model_dump_json(indent=2))
        
        # Save agent claims
        for agent_id, claims in agent_claims.items():
            filename = f"claims_{agent_id}_{timestamp}.json"
            with open(os.path.join(event_dir, filename), "w") as f:
                f.write(claims.model_dump_json(indent=2))
        
        # Save convergence metrics
        metrics_file = os.path.join(event_dir, f"convergence_{timestamp}.json")
        with open(metrics_file, "w") as f:
            f.write(convergence_metrics.model_dump_json(indent=2))
        
        # Save metadata
        metadata = {
            "event_id": str(event_id),
            "timestamp": timestamp,
            "incident_text_hash": hash(incident_text),
            "artifacts": {
                "evidence": [f"evidence_{agent_id}_{timestamp}.json" 
                           for agent_id in evidence_extractions.keys()],
                "claims": [f"claims_{agent_id}_{timestamp}.json" 
                          for agent_id in agent_claims.keys()],
                "convergence": f"convergence_{timestamp}.json"
            }
        }
        
        with open(os.path.join(event_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _prepare_final_output(self, incident_text: str,
                            convergence_metrics: ConvergenceMetrics,
                            evidence_extractions: Dict[str, EvidenceExtraction],
                            agent_claims: Dict[str, AgentClaims]) -> Dict:
        """Prepare the final output for the user"""
        # Count total evidence items
        total_evidence = sum(
            len(extraction.evidence) 
            for extraction in evidence_extractions.values()
        )
        
        # Get agent label explanations
        agent_explanations = {}
        for agent_id, claims in agent_claims.items():
            label = getattr(convergence_metrics.agent_labels, agent_id)
            agent_explanations[agent_id] = {
                "label": label,
                "confidence": claims.agent_confidence,
                "num_claims": len(claims.claims),
                "num_gaps": len(claims.gaps),
                "label_score": claims.compute_label_score()
            }
        
        return {
            "event_id": str(convergence_metrics.event_id),
            "timestamp": datetime.utcnow().isoformat(),
            "incident_preview": incident_text[:500] + "..." if len(incident_text) > 500 else incident_text,
            "summary": {
                "total_evidence_items": total_evidence,
                "agent_labels": agent_explanations,
                "evidence_overlap": convergence_metrics.evidence_intersection,
                "disagreement_entropy": convergence_metrics.disagreement_entropy,
                "residual_disagreement": convergence_metrics.residual_disagreement
            },
            "decision": convergence_metrics.decision,
            "epistemic_status": self._get_epistemic_status(convergence_metrics.decision["label"]),
            "artifacts_location": os.path.join(
                self.storage_path, 
                str(convergence_metrics.event_id)
            )
        }
    
    def _get_epistemic_status(self, label: FinalLabel) -> str:
        """Get human-readable epistemic status"""
        if label == FinalLabel.UNCERTAIN:
            return "EPISTEMIC_UNCERTAINTY: Insufficient evidence or excessive disagreement"
        elif label == FinalLabel.BENIGN:
            return "CONSENSUS_BENIGN: Evidence favors non-malicious explanation"
        else:
            return "CONSENSUS_MALICIOUS: Evidence favors malicious explanation"