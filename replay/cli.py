# src/replay/cli.py
import argparse
import json
from pathlib import Path
from typing import Optional
from tabulate import tabulate

from .replay_engine import ArtifactReplayEngine

class ReplayCLI:
    """Command-line interface for artifact replay"""
    
    def __init__(self, artifacts_path: Path):
        self.engine = ArtifactReplayEngine(artifacts_path)
    
    def list_events(self, limit: int = 20) -> None:
        """List available events"""
        event_dirs = self.engine.find_event_directories()
        
        print(f"\nFound {len(event_dirs)} events in {self.engine.artifacts_base_path}\n")
        
        events_info = []
        for event_dir in event_dirs[:limit]:
            try:
                artifacts = self.engine.load_event_artifacts(event_dir)
                if artifacts:
                    # Get decision from convergence metrics
                    decision = "UNKNOWN"
                    confidence = 0.0
                    if artifacts.get('convergence_metrics'):
                        decision = artifacts['convergence_metrics'].decision['label']
                        confidence = artifacts['convergence_metrics'].decision['confidence']
                    
                    events_info.append({
                        'event_id': event_dir.name[:8] + "...",
                        'incident_preview': artifacts['incident_text'][:50] + "...",
                        'agents': len(artifacts.get('evidence_extractions', {})),
                        'decision': decision,
                        'confidence': f"{confidence:.2f}",
                        'timestamp': datetime.fromtimestamp(event_dir.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
            except Exception as e:
                events_info.append({
                    'event_id': event_dir.name[:8] + "...",
                    'incident_preview': f"Error: {str(e)[:30]}",
                    'agents': 0,
                    'decision': "ERROR",
                    'confidence': "0.00",
                    'timestamp': "N/A"
                })
        
        print(tabulate(events_info, headers="keys", tablefmt="grid"))
    
    def replay_event(self, event_id: str, recalculate: bool = True, 
                    output: Optional[Path] = None) -> None:
        """Replay a specific event"""
        print(f"\nReplaying event: {event_id}")
        
        try:
            result = self.engine.replay_event(event_id, recalculate)
            
            print(f"\nStatus: {result['status']}")
            print(f"Decision: {result['convergence_metrics'].decision['label']}")
            print(f"Confidence: {result['convergence_metrics'].decision['confidence']:.3f}")
            print(f"Residual Disagreement: {result['convergence_metrics'].residual_disagreement:.3f}")
            
            if result['convergence_metrics'].decision['reason_codes']:
                print(f"Reason Codes: {', '.join(result['convergence_metrics'].decision['reason_codes'])}")
            
            if 'comparison_with_original' in result:
                comparison = result['comparison_with_original']
                if comparison['identical']:
                    print("\n✅ Deterministic check PASSED: Recomputed metrics match original")
                else:
                    print("\n⚠️  Deterministic check FAILED: Differences found")
                    for key, diff in comparison['differences'].items():
                        print(f"  {key}: {diff['original']} → {diff['recomputed']}")
            
            if output:
                output_path = Path(output)
                with open(output_path, 'w') as f:
                    json.dump({
                        'event_id': event_id,
                        'replay_result': result,
                        'convergence_metrics': result['convergence_metrics'].model_dump()
                    }, f, indent=2, default=str)
                print(f"\nResults saved to: {output_path}")
                
        except Exception as e:
            print(f"\n❌ Error replaying event: {e}")
    
    def validate_contracts(self, event_id: str) -> None:
        """Validate artifact contracts for an event"""
        print(f"\nValidating artifact contracts for: {event_id}")
        
        result = self.engine.validate_artifact_contracts(event_id)
        
        if result['valid']:
            print("✅ All artifact contracts satisfied")
        else:
            print("❌ Artifact contracts violated")
            
            if result['missing_artifacts']:
                print("\nMissing artifacts:")
                for artifact in result['missing_artifacts']:
                    print(f"  - {artifact}")
            
            if result['invalid_artifacts']:
                print("\nInvalid artifacts:")
                for artifact in result['invalid_artifacts']:
                    print(f"  - {artifact}")
        
        print("\nDetailed checks:")
        for check, passed in result['checks'].items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
    
    def batch_validate(self) -> None:
        """Batch validate all events"""
        event_dirs = self.engine.find_event_directories()
        
        print(f"\nBatch validating {len(event_dirs)} events...\n")
        
        results = {
            'total': len(event_dirs),
            'valid': 0,
            'invalid': 0,
            'details': []
        }
        
        for event_dir in event_dirs:
            event_id = event_dir.name
            validation = self.engine.validate_artifact_contracts(event_id)
            
            results['details'].append({
                'event_id': event_id[:8] + "...",
                'valid': validation['valid'],
                'missing_count': len(validation.get('missing_artifacts', [])),
                'invalid_count': len(validation.get('invalid_artifacts', []))
            })
            
            if validation['valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        
        print(f"Valid events: {results['valid']}/{results['total']}")
        print(f"Invalid events: {results['invalid']}/{results['total']}")
        
        if results['invalid'] > 0:
            print("\nInvalid events details:")
            invalid_events = [d for d in results['details'] if not d['valid']]
            print(tabulate(invalid_events, headers="keys", tablefmt="grid"))
    
    def export_event(self, event_id: str, output_dir: Path) -> None:
        """Export event for reproducibility"""
        print(f"\nExporting event: {event_id}")
        
        try:
            export_path = self.engine.export_event_for_reproducibility(
                event_id, 
                Path(output_dir)
            )
            
            print(f"✅ Export complete")
            print(f"Export directory: {export_path}")
            print(f"Manifest: {export_path / 'manifest.json'}")
            
            # Show manifest
            manifest_path = export_path / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                print(f"\nManifest contents:")
                print(f"  Event ID: {manifest['event_id']}")
                print(f"  Export timestamp: {manifest['export_timestamp']}")
                print(f"  System version: {manifest['system_version']}")
                print(f"  Engine hash: {manifest['convergence_engine_hash']}")
                print(f"  Directory hash: {manifest['directory_hash']}")
                print(f"  Artifacts: {len(manifest['artifacts'])} files")
                
        except Exception as e:
            print(f"❌ Export failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Artifact Replay System for Self-Arguing Multi-Agent Analyst"
    )
    parser.add_argument(
        "--artifacts-path", 
        default="./artifacts",
        help="Path to artifacts directory (default: ./artifacts)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available events")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum events to list")
    
    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay an event")
    replay_parser.add_argument("event_id", help="Event ID to replay")
    replay_parser.add_argument("--no-recalculate", action="store_true", 
                             help="Don't recalculate, just load existing")
    replay_parser.add_argument("--output", help="Output file for results")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate artifact contracts")
    validate_parser.add_argument("event_id", help="Event ID to validate")
    
    # Batch validate command
    batch_parser = subparsers.add_parser("batch-validate", help="Batch validate all events")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export event for reproducibility")
    export_parser.add_argument("event_id", help="Event ID to export")
    export_parser.add_argument("--output-dir", default="./exports", 
                              help="Output directory for export")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = ReplayCLI(Path(args.artifacts_path))
    
    # Execute command
    if args.command == "list":
        cli.list_events(args.limit)
    elif args.command == "replay":
        cli.replay_event(args.event_id, not args.no_recalculate, args.output)
    elif args.command == "validate":
        cli.validate_contracts(args.event_id)
    elif args.command == "batch-validate":
        cli.batch_validate()
    elif args.command == "export":
        cli.export_event(args.event_id, Path(args.output_dir))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()