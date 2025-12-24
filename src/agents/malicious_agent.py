from src.agents.base_agent import BaseAgent
from src.roles.registry import RoleRegistry

class MaliciousAgent(BaseAgent):
    def __init__(self):
        role = RoleRegistry().get("malicious")
        if not role:
            raise ValueError("Role 'malicious' not found in registry")
        super().__init__(role)