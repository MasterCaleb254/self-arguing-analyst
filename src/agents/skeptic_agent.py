from src.agents.base_agent import BaseAgent
from src.roles.registry import RoleRegistry

class SkepticAgent(BaseAgent):
    def __init__(self):
        role = RoleRegistry().get("skeptic")
        if not role:
            raise ValueError("Role 'skeptic' not found in registry")
        super().__init__(role)