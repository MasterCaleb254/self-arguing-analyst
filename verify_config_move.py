
import sys
import os

# Ensure root is in path
sys.path.append(os.getcwd())

print("Attempting to import settings from src.config.settings...")
try:
    from src.config.settings import settings
    print(f"Successfully imported settings. Model: {settings.openai_model}")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Other error: {e}")
    sys.exit(1)

from src.roles.registry import Role, RoleRegistry
from src.agents.base_agent import BaseAgent

print("Attempting to initialize BaseAgent with Role...")
try:
    role = Role(
        name="test",
        evidence_extraction_system_prompt="sys prompt",
        claims_generation_system_prompt="claims prompt",
        default_stance="test"
    )
    agent = BaseAgent(role=role)
    print("BaseAgent initialized successfully.")
except Exception as e:
    print(f"Failed to initialize BaseAgent: {e}")
    import traceback
    traceback.print_exc()
