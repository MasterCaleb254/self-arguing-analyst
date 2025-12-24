# src/roles/registry.py
from typing import Dict, List, Optional, Type
from dataclasses import dataclass
from enum import Enum
import importlib

class AgentRole(str, Enum):
    BENIGN = "benign"
    MALICIOUS = "malicious" 
    SKEPTIC = "skeptic"
    THREAT_INTEL = "threat_intel"
    BASE_RATE = "base_rate"
    FORENSIC = "forensic"

@dataclass
class Role:
    """Configuration for a pluggable agent role"""
    name: str
    description: str = ""
    evidence_extraction_system_prompt: str = ""
    claims_generation_system_prompt: str = ""
    default_stance: str = ""
    weight: float = 1.0  # For weighted voting
    enabled: bool = True

class RoleRegistry:
    """Registry for pluggable agent roles"""
    
    _instance = None
    _roles: Dict[str, Role] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RoleRegistry, cls).__new__(cls)
            cls._instance._initialize_default_roles()
        return cls._instance
    
    def _initialize_default_roles(self):
        """Initialize default agent roles"""
        default_roles = {
            "benign": Role(
                name="benign",
                description="Focuses on non-malicious explanations",
                evidence_extraction_system_prompt="...",
                claims_generation_system_prompt="...",
                default_stance="BENIGN_HYPOTHESIS"
            ),
            "malicious": Role(
                name="malicious",
                description="Focuses on indicators of compromise",
                evidence_extraction_system_prompt="...",
                claims_generation_system_prompt="...",
                default_stance="MALICIOUS_HYPOTHESIS"
            ),
            "skeptic": Role(
                name="skeptic",
                description="Challenges assumptions, emphasizes evidence gaps",
                evidence_extraction_system_prompt="...",
                claims_generation_system_prompt="...",
                default_stance="SKEPTICAL_HYPOTHESIS"
            ),
            "threat_intel": Role(
                name="threat_intel",
                description="Focuses on threat intelligence and TTPs",
                evidence_extraction_system_prompt="""You are a Threat Intelligence Analyst.
                Focus on extracting indicators that match known threat actor TTPs.
                Prioritize IOCs with threat intelligence context.""",
                claims_generation_system_prompt="""You are a Threat Intelligence Analyst.
                Analyze evidence through the lens of known threat actor behaviors.
                Reference MITRE ATT&CK techniques and threat groups when applicable.""",
                default_stance="MALICIOUS_HYPOTHESIS",
                weight=1.2  # Threat intel gets slightly more weight
            ),
            "base_rate": Role(
                name="base_rate",
                description="Applies base rate fallacy awareness",
                evidence_extraction_system_prompt="""You are a Base Rate Analyst.
                Focus on statistical likelihoods and prior probabilities.
                Extract evidence that helps assess base rates.""",
                claims_generation_system_prompt="""You are a Base Rate Analyst.
                Consider how common benign vs malicious explanations are.
                Apply Bayesian reasoning and avoid base rate fallacy.""",
                default_stance="SKEPTICAL_HYPOTHESIS"
            )
        }
        
        for name, config in default_roles.items():
            self.register(config)
    
    def register(self, config: Role):
        """Register a new agent role"""
        self._roles[config.name] = config
    
    def get(self, name: str) -> Optional[Role]:
        """Get role configuration by name"""
        return self._roles.get(name)
    
    def list(self) -> List[str]:
        """List all registered role names"""
        return list(self._roles.keys())
    
    def load_from_module(self, module_path: str):
        """Load roles from an external module"""
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, 'register_roles'):
                module.register_roles(self)
        except ImportError as e:
            print(f"[RoleRegistry] Failed to load module {module_path}: {e}")
    
    def create_agent_set(self, role_names: List[str] = None) -> Dict[str, Role]:
        """Create a set of agents from role names"""
        if role_names is None:
            role_names = ["benign", "malicious", "skeptic"]
        
        agents = {}
        for name in role_names:
            config = self.get(name)
            if config and config.enabled:
                agents[name] = config
        
        return agents