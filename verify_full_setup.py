
import sys
import os
import asyncio

# Ensure root is in path
sys.path.append(os.getcwd())

from src.orchestrator import EventOrchestrator
from src.roles.registry import RoleRegistry

async def test_setup():
    print("Testing EventOrchestrator setup...")
    try:
        # Check if roles are registered
        registry = RoleRegistry()
        print(f"Registered roles: {registry.list()}")
        
        # Initialize orchestrator
        orchestrator = EventOrchestrator()
        print("Orchestrator initialized.")
        
        # Check agents
        for agent_id, agent in orchestrator.agents.items():
            print(f"Agent {agent_id} initialized with role: {agent.role.name}")
            assert agent.role.name == agent_id
            
        print("Setup verification successful!")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_setup())
