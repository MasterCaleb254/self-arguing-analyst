from src.agents.base_agent import BaseAgent
from src.roles.registry import RoleRegistry

class BenignAgent(BaseAgent):
    def __init__(self):
        role = RoleRegistry().get("benign")
        if not role:
            raise ValueError("Role 'benign' not found in registry")
        super().__init__(role)