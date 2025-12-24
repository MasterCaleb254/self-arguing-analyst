# api/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
import asyncio

from src.orchestrator_enhanced import EnhancedOrchestrator, AnalysisConfiguration

app = FastAPI(
    title="Self-Arguing Multi-Agent Analyst API",
    description="Epistemic disagreement as a first-class signal",
    version="1.0.0"
)

# Global orchestrator instance
orchestrator = None

class AnalysisRequest(BaseModel):
    incident_text: str = Field(..., min_length=10, description="Cybersecurity incident description")
    event_id: Optional[str] = None
    enable_mitre: bool = False
    roles: List[str] = ["benign", "malicious", "skeptic"]
    priority: str = "normal"  # normal, high

class AnalysisResponse(BaseModel):
    event_id: str
    status: str
    decision: dict
    summary: dict
    epistemic_status: str
    artifacts_location: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    queue_position: Optional[int] = None

class AnalysisQueue:
    """Simple in-memory analysis queue"""
    def __init__(self):
        self.queue = asyncio.Queue()
        self.results = {}
        self.processing = set()
    
    async def add_request(self, request_id: str, request: AnalysisRequest):
        await self.queue.put((request_id, request))
    
    async def process_next(self):
        if not self.queue.empty():
            request_id, request = await self.queue.get()
            self.processing.add(request_id)
            return request_id, request
        return None, None
    
    def complete_request(self, request_id: str, result: dict):
        self.results[request_id] = result
        self.processing.discard(request_id)
    
    def get_result(self, request_id: str) -> Optional[dict]:
        return self.results.get(request_id)

# Initialize queue
analysis_queue = AnalysisQueue()

@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    global orchestrator
    config = AnalysisConfiguration(
        enable_mitre_enrichment=False,  # Controlled per request
        convergence_thresholds={
            "consensus_threshold": 0.2,
            "jaccard_threshold": 0.2,
            "residual_disagreement_threshold": 0.35
        }
    )
    orchestrator = EnhancedOrchestrator(config)
    
    # Start background processor
    asyncio.create_task(process_analysis_queue())

async def process_analysis_queue():
    """Background task to process analysis queue"""
    while True:
        request_id, request = await analysis_queue.process_next()
        if request_id and request:
            try:
                # Configure orchestrator for this request
                config = AnalysisConfiguration(
                    role_names=request.roles,
                    enable_mitre_enrichment=request.enable_mitre
                )
                orchestrator.config = config
                
                # Run analysis
                result = await orchestrator.analyze_incident(
                    request.incident_text,
                    UUID(request.event_id) if request.event_id else None
                )
                
                analysis_queue.complete_request(request_id, {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                analysis_queue.complete_request(request_id, {
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.utcnow().isoformat()
                })
        
        await asyncio.sleep(1)  # Prevent tight loop

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_incident(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Submit incident for analysis"""
    request_id = str(uuid4())
    
    if request.priority == "high":
        # Immediate processing for high priority
        try:
            config = AnalysisConfiguration(
                role_names=request.roles,
                enable_mitre_enrichment=request.enable_mitre
            )
            orchestrator.config = config
            
            result = await orchestrator.analyze_incident(
                request.incident_text,
                UUID(request.event_id) if request.event_id else None
            )
            
            return AnalysisResponse(
                event_id=result['event_id'],
                status="completed",
                decision=result['decision'],
                summary=result['summary'],
                epistemic_status=result['epistemic_status'],
                artifacts_location=result['artifacts_location']
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    else:
        # Queue for normal priority
        await analysis_queue.add_request(request_id, request)
        
        queue_position = analysis_queue.queue.qsize()
        
        return AnalysisResponse(
            event_id=request_id,
            status="queued",
            decision={},
            summary={},
            epistemic_status="PENDING_ANALYSIS",
            estimated_completion=datetime.utcnow(),  # Simplified
            queue_position=queue_position
        )

@app.get("/results/{event_id}")
async def get_results(event_id: str):
    """Get analysis results"""
    result = analysis_queue.get_result(event_id)
    if not result:
        # Check if it's still processing
        if event_id in analysis_queue.processing:
            return {
                "event_id": event_id,
                "status": "processing",
                "message": "Analysis in progress"
            }
        else:
            # Check if it exists in orchestrator storage
            try:
                # This would need implementation to load from storage
                raise HTTPException(status_code=404, detail="Result not found")
            except:
                raise HTTPException(status_code=404, detail="Result not found")
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "event_id": event_id,
        "status": result["status"],
        "result": result.get("result"),
        "completed_at": result.get("completed_at")
    }

@app.get("/metrics")
async def get_system_metrics():
    """Get system metrics"""
    return {
        "queue_size": analysis_queue.queue.qsize(),
        "processing": len(analysis_queue.processing),
        "completed": len(analysis_queue.results),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/evaluate")
async def run_evaluation():
    """Run evaluation on synthetic dataset (admin endpoint)"""
    # This would trigger the evaluation pipeline
    # In production, this should be protected
    return {"status": "evaluation_started", "message": "Check logs for progress"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)