# quick_test.py
import asyncio
from src.orchestrator import EventOrchestrator

async def test_system():
    orchestrator = EventOrchestrator()
    
    test_incident = """
    User reported suspicious email with attachment.
    Attachment file: invoice.exe from domain shady-invoices.net
    File executed and created scheduled task "MicrosoftUpdates".
    Network connection to 45.67.89.123 on port 8443.
    Windows Defender flagged file as Trojan:Win32/Fareit.C
    User claims they didn't open the attachment.
    """
    
    result = await orchestrator.analyze_incident(test_incident)
    return result

if __name__ == "__main__":
    result = asyncio.run(test_system())
    print(f"Final Decision: {result['decision']['label']}")
    print(f"Confidence: {result['decision']['confidence']:.2f}")