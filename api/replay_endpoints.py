# api/replay_endpoints.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

from src.replay.replay_engine import ArtifactReplayEngine

router = APIRouter(prefix="/replay", tags=["replay"])

# Global replay engine
replay_engine = None

class ReplayRequest(BaseModel):
    event_id: str
    recalculate: bool = True

class BatchReplayRequest(BaseModel):
    event_ids: Optional[List[str]] = None
    recalculate: bool = True

class ExportRequest(BaseModel):
    event_id: str
    output_dir: str = "./exports"

@router.on_event("startup")
async def startup_event():
    """Initialize replay engine on startup"""
    global replay_engine
    artifacts_path = Path("./artifacts")
    artifacts_path.mkdir(exist_ok=True)
    replay_engine = ArtifactReplayEngine(artifacts_path)

@router.get("/events")
async def list_events(limit: int = 20):
    """List available events for replay"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    event_dirs = replay_engine.find_event_directories()
    events = []
    
    for event_dir in event_dirs[:limit]:
        artifacts = replay_engine.load_event_artifacts(event_dir)
        if artifacts:
            events.append({
                "event_id": event_dir.name,
                "incident_preview": artifacts['incident_text'][:100] + "..." if len(artifacts['incident_text']) > 100 else artifacts['incident_text'],
                "agents": list(artifacts['evidence_extractions'].keys()),
                "artifact_count": len(artifacts.get('evidence_extractions', {})) + len(artifacts.get('agent_claims', {}))
            })
    
    return {
        "total_events": len(event_dirs),
        "events_shown": min(limit, len(event_dirs)),
        "events": events
    }

@router.post("/replay")
async def replay_event(request: ReplayRequest):
    """Replay a specific event"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    try:
        result = replay_engine.replay_event(request.event_id, request.recalculate)
        
        # Convert to serializable format
        result_serializable = {
            "event_id": result["event_id"],
            "status": result["status"],
            "decision": result["convergence_metrics"].decision,
            "residual_disagreement": result["convergence_metrics"].residual_disagreement,
            "deterministic_check": result.get("deterministic_check", "N/A")
        }
        
        if "comparison_with_original" in result:
            result_serializable["comparison"] = result["comparison_with_original"]
        
        return result_serializable
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-replay")
async def batch_replay(request: BatchReplayRequest, background_tasks: BackgroundTasks):
    """Batch replay multiple events"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    try:
        result = replay_engine.batch_replay(request.event_ids, request.recalculate)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/{event_id}")
async def validate_event(event_id: str):
    """Validate artifact contracts for an event"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    try:
        result = replay_engine.validate_artifact_contracts(event_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch-validate")
async def batch_validate():
    """Batch validate all events"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    try:
        event_dirs = replay_engine.find_event_directories()
        results = []
        
        for event_dir in event_dirs[:50]:  # Limit to 50 for performance
            result = replay_engine.validate_artifact_contracts(event_dir.name)
            results.append({
                "event_id": event_dir.name,
                "valid": result["valid"],
                "missing_artifacts": result.get("missing_artifacts", []),
                "invalid_artifacts": result.get("invalid_artifacts", [])
            })
        
        return {
            "total_events": len(event_dirs),
            "validated": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_event(request: ExportRequest):
    """Export event for reproducibility"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    try:
        export_dir = replay_engine.export_event_for_reproducibility(
            request.event_id,
            Path(request.output_dir)
        )
        
        # Read manifest
        manifest_path = export_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        
        return {
            "event_id": request.event_id,
            "export_directory": str(export_dir),
            "manifest": manifest
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deterministic-check/{event_id}")
async def deterministic_check(event_id: str):
    """Check if replay produces identical results"""
    if not replay_engine:
        raise HTTPException(status_code=500, detail="Replay engine not initialized")
    
    try:
        # First replay
        result1 = replay_engine.replay_event(event_id, recalculate=True)
        
        # Second replay (should be identical)
        result2 = replay_engine.replay_event(event_id, recalculate=True)
        
        comparison = replay_engine._compare_convergence_results(
            result1["convergence_metrics"],
            result2["convergence_metrics"]
        )
        
        return {
            "event_id": event_id,
            "deterministic": comparison["identical"],
            "decision_match": comparison["decision_match"],
            "confidence_difference": comparison["confidence_diff"],
            "differences": comparison["differences"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))