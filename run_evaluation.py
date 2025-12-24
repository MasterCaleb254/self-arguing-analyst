import asyncio
from pathlib import Path
from src.evaluation.harness import LabeledDataset, EvaluationHarness
from src.orchestrator import EventOrchestrator

async def main():
    # Load dataset
    dataset_path = Path("data/labeled_incidents.jsonl")
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}. Please provide a labeled dataset.")
        return
    
    dataset = LabeledDataset(dataset_path)
    dataset.load()
    
    print(f"Loaded {len(dataset)} incidents.")
    
    # Initialize orchestrator
    orchestrator = EventOrchestrator()
    
    # Run evaluation
    harness = EvaluationHarness(dataset, orchestrator)
    await harness.evaluate(limit=10)  # Limit for testing, remove for full evaluation
    
    # Compute metrics
    metrics = harness.compute_metrics()
    
    print("\nEvaluation Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())