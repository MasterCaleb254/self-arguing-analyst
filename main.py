# main.py
import asyncio
import json
import sys
from uuid import UUID
from pathlib import Path

from src.orchestrator import EventOrchestrator
from src.replay.replay_engine import ArtifactReplayEngine
from src.config.settings import settings

def display_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("SELF-ARGUING MULTI-AGENT ANALYST")
    print("Epistemic Disagreement as First-Class Signal")
    print("="*60)
    print("\nMain Menu:")
    print("1. Analyze new incident")
    print("2. Replay existing analysis")
    print("3. Validate artifact contracts")
    print("4. Batch replay all events")
    print("5. Export event for reproducibility")
    print("6. Run evaluation on synthetic dataset")
    print("7. Exit")
    print("\n" + "-"*60)

async def analyze_new_incident():
    """Analyze a new incident"""
    print("\n[Mode: Analyze New Incident]")
    
    if len(sys.argv) > 2 and sys.argv[2] == "--file":
        # Read from file
        file_path = sys.argv[3]
        with open(file_path, 'r') as f:
            incident_text = f.read()
    else:
        # Interactive input
        print("Enter incident text (Ctrl+D to finish):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            incident_text = "\n".join(lines)
    
    if not incident_text.strip():
        print("No incident text provided.")
        return
    
    orchestrator = EventOrchestrator()
    result = await orchestrator.analyze_incident(incident_text)
    
    print("\n" + "="*60)
    print("ANALYSIS RESULT")
    print("="*60)
    print(f"Event ID: {result['event_id']}")
    print(f"Decision: {result['decision']['label']}")
    print(f"Confidence: {result['decision']['confidence']:.2f}")
    print(f"Residual Disagreement: {result['summary']['residual_disagreement']:.2f}")
    print(f"Epistemic Status: {result['epistemic_status']}")
    
    if result['decision']['reason_codes']:
        print(f"Reason Codes: {', '.join(result['decision']['reason_codes'])}")
    
    print(f"\nArtifacts saved to: {result['artifacts_location']}")

def replay_existing_analysis():
    """Replay an existing analysis"""
    print("\n[Mode: Replay Existing Analysis]")
    
    # List available events
    replay_engine = ArtifactReplayEngine(Path(settings.artifact_storage_path))
    event_dirs = replay_engine.find_event_directories()
    
    if not event_dirs:
        print("No existing events found.")
        return
    
    print(f"\nFound {len(event_dirs)} events:")
    for i, event_dir in enumerate(event_dirs[:10], 1):
        print(f"{i}. {event_dir.name} ({event_dir.stat().st_size} bytes)")
    
    print("\nEnter event ID or number: ", end="")
    choice = input().strip()
    
    try:
        if choice.isdigit():
            event_id = event_dirs[int(choice)-1].name
        else:
            event_id = choice
        
        result = replay_engine.replay_event(event_id, recalculate=True)
        
        print("\n" + "="*60)
        print("REPLAY RESULT")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Decision: {result['convergence_metrics'].decision['label']}")
        print(f"Confidence: {result['convergence_metrics'].decision['confidence']:.3f}")
        print(f"Residual Disagreement: {result['convergence_metrics'].residual_disagreement:.3f}")
        
        if result['convergence_metrics'].decision['reason_codes']:
            print(f"Reason Codes: {', '.join(result['convergence_metrics'].decision['reason_codes'])}")
        
        if 'comparison_with_original' in result:
            comparison = result['comparison_with_original']
            if comparison['identical']:
                print("\n✅ Deterministic check PASSED")
            else:
                print(f"\n⚠️  Deterministic check FAILED ({len(comparison['differences'])} differences)")
    
    except Exception as e:
        print(f"Error: {e}")

def validate_artifact_contracts():
    """Validate artifact contracts"""
    print("\n[Mode: Validate Artifact Contracts]")
    
    replay_engine = ArtifactReplayEngine(Path(settings.artifact_storage_path))
    
    print("Enter event ID (or 'all' for batch validation): ", end="")
    choice = input().strip()
    
    if choice.lower() == 'all':
        result = replay_engine.batch_replay([], recalculate=False)
        valid_count = sum(1 for e in result['events'] if 'deterministic_check' in e and e['deterministic_check'] == 'identical')
        print(f"\nBatch validation complete:")
        print(f"  Total events: {result['total_events']}")
        print(f"  Successful: {result['successful_replays']}")
        print(f"  Failed: {result['failed_replays']}")
        print(f"  Deterministic: {valid_count}")
    else:
        result = replay_engine.validate_artifact_contracts(choice)
        print(f"\nValidation for event {choice}:")
        print(f"  Valid: {result['valid']}")
        if not result['valid']:
            print(f"  Missing artifacts: {result.get('missing_artifacts', [])}")
            print(f"  Invalid artifacts: {result.get('invalid_artifacts', [])}")

async def main():
    """Main application loop"""
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "replay":
            replay_existing_analysis()
        elif sys.argv[1] == "validate":
            validate_artifact_contracts()
        elif sys.argv[1] == "analyze":
            await analyze_new_incident()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python main.py [analyze|replay|validate]")
        return
    
    # Interactive mode
    while True:
        display_menu()
        
        try:
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                await analyze_new_incident()
            elif choice == "2":
                replay_existing_analysis()
            elif choice == "3":
                validate_artifact_contracts()
            elif choice == "4":
                print("\nBatch replay - this may take a while...")
                replay_engine = ArtifactReplayEngine(Path(settings.artifact_storage_path))
                result = replay_engine.batch_replay([], recalculate=True)
                print(f"\nBatch replay complete:")
                print(f"  Total: {result['total_events']}")
                print(f"  Successful: {result['successful_replays']}")
                print(f"  Failed: {result['failed_replays']}")
            elif choice == "5":
                print("\nExport event for reproducibility")
                event_id = input("Enter event ID: ").strip()
                replay_engine = ArtifactReplayEngine(Path(settings.artifact_storage_path))
                try:
                    export_dir = replay_engine.export_event_for_reproducibility(
                        event_id, 
                        Path("./exports")
                    )
                    print(f"Exported to: {export_dir}")
                except Exception as e:
                    print(f"Error: {e}")
            elif choice == "6":
                print("\nRunning evaluation on synthetic dataset...")
                # This would call the evaluation harness
                print("Feature coming soon!")
            elif choice == "7":
                print("\nExiting. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())