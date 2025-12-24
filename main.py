# main.py
import asyncio
import json
import sys
from uuid import UUID
from pathlib import Path

from src.orchestrator import EventOrchestrator
from src.config.settings import settings

def load_example_incidents():
    """Example cybersecurity incidents for testing"""
    return [
        {
            "id": "incident_1",
            "text": """At 14:30 UTC, user jsmith@company.com downloaded a file from suspicious-domain.com. 
            File hash: a1b2c3d4e5f6789012345678901234567890abcde. 
            The file was executed and created registry key HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater.
            Network traffic detected to 192.168.1.100 on port 443. 
            No antivirus alerts triggered."""
        },
        {
            "id": "incident_2", 
            "text": """System administrator performed scheduled maintenance on server SRV-DB-01.
            Installed Windows updates KB5005565 and KB5006670.
            Created backup file at C:\\Backups\\db_backup_20231027.bak.
            Restarted SQL Server service. 
            All activities logged in SIEM with admin credentials."""
        },
        {
            "id": "incident_3",
            "text": """Unknown PowerShell script executed from C:\\Users\\Public\\temp.ps1.
            Script attempted to disable Windows Defender real-time protection.
            Connection attempted to external IP 185.220.101.204 on port 8080.
            Script source unknown. User account appears compromised."""
        }
    ]

async def main():
    print("=" * 60)
    print("Self-Arguing Multi-Agent Analyst")
    print("Epistemic Disagreement as First-Class Signal")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = EventOrchestrator()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Read incident from file
        file_path = sys.argv[1]
        with open(file_path, 'r') as f:
            incident_text = f.read()
        
        result = await orchestrator.analyze_incident(incident_text)
        print("\n" + "=" * 60)
        print("ANALYSIS RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
        
    else:
        # Run example incidents
        incidents = load_example_incidents()
        
        for incident in incidents:
            print(f"\n{'='*60}")
            print(f"Analyzing Incident: {incident['id']}")
            print(f"{'='*60}")
            
            result = await orchestrator.analyze_incident(incident['text'])
            
            print(f"\nDecision: {result['decision']['label']}")
            print(f"Confidence: {result['decision']['confidence']:.2f}")
            print(f"Residual Disagreement: {result['summary']['residual_disagreement']:.2f}")
            print(f"Epistemic Status: {result['epistemic_status']}")
            
            if result['decision']['reason_codes']:
                print(f"Reason Codes: {', '.join(result['decision']['reason_codes'])}")
            
            print(f"\nAgent Labels:")
            for agent, info in result['summary']['agent_labels'].items():
                print(f"  {agent}: {info['label']} (conf: {info['confidence']:.2f})")

if __name__ == "__main__":
    asyncio.run(main())