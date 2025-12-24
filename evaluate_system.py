# evaluate_system.py
import asyncio
import json
from pathlib import Path
from datetime import datetime
import argparse

from src.orchestrator_enhanced import EnhancedOrchestrator, AnalysisConfiguration
from src.evaluation.harness import EvaluationHarness
from src.synthetic.generator import SyntheticIncidentGenerator
from src.visualization.plots import VisualizationEngine

async def run_evaluation():
    """Complete evaluation pipeline"""
    parser = argparse.ArgumentParser(description="Evaluate Self-Arguing Multi-Agent Analyst")
    parser.add_argument("--dataset", type=str, help="Path to labeled dataset")
    parser.add_argument("--generate", type=int, help="Generate synthetic dataset of given size")
    parser.add_argument("--config", type=str, help="Configuration file")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = output_dir / timestamp
    results_dir.mkdir()
    
    # Load or generate dataset
    if args.generate:
        print(f"[Evaluation] Generating synthetic dataset of size {args.generate}")
        generator = SyntheticIncidentGenerator()
        incidents = generator.generate_dataset(size=args.generate)
        dataset_path = results_dir / "synthetic_dataset.jsonl"
        generator.save_dataset(incidents, dataset_path)
    elif args.dataset:
        dataset_path = Path(args.dataset)
    else:
        print("[Evaluation] No dataset provided. Using default synthetic dataset.")
        generator = SyntheticIncidentGenerator()
        incidents = generator.generate_dataset(size=50)
        dataset_path = results_dir / "default_dataset.jsonl"
        generator.save_dataset(incidents, dataset_path)
    
    # Load configuration
    config = AnalysisConfiguration()
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            config = AnalysisConfiguration(**config_data)
    
    # Initialize orchestrator
    print(f"[Evaluation] Initializing orchestrator with roles: {config.role_names}")
    orchestrator = EnhancedOrchestrator(
        config=config,
        storage_path=str(results_dir / "artifacts")
    )
    
    # Run evaluation
    harness = EvaluationHarness(orchestrator)
    results = await harness.evaluate_dataset(dataset_path)
    
    # Generate report
    report = harness.generate_report()
    report_path = results_dir / "evaluation_report.json"
    harness.save_report(report_path)
    
    # Generate visualizations
    print("[Evaluation] Generating visualizations...")
    viz = VisualizationEngine()
    
    # Load results for visualization
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    # Create plots
    plots_dir = results_dir / "plots"
    plots_dir.mkdir()
    
    # Plot 1: Disagreement dynamics
    fig1 = viz.plot_disagreement_dynamics(
        report_data['detailed_results'],
        plots_dir / "disagreement_dynamics.html"
    )
    
    # Plot 2: Agent agreement matrix
    fig2 = viz.plot_agent_agreement_matrix(
        report_data['detailed_results'],
        plots_dir / "agent_agreement.png"
    )
    
    # Plot 3: Epistemic uncertainty breakdown
    fig3 = viz.plot_epistemic_uncertainty_breakdown(
        report_data['detailed_results'],
        plots_dir / "uncertainty_breakdown.png"
    )
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    for key, value in report_data['metrics'].items():
        if isinstance(value, float):
            print(f"{key:30}: {value:.4f}")
        else:
            print(f"{key:30}: {value}")
    
    # Save configuration
    config_path = results_dir / "configuration.json"
    with open(config_path, 'w') as f:
        json.dump(config.__dict__, f, indent=2, default=str)
    
    print(f"\n[Evaluation] Complete! Results saved to: {results_dir}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())