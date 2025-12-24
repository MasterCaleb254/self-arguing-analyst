# config/settings.py
import os
from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    
    # Agent configurations
    agent_temperature: float = 0.1  # Low temperature for consistency
    max_retries: int = 3
    
    # Convergence thresholds
    consensus_threshold: float = 0.2
    jaccard_threshold: float = 0.2
    residual_disagreement_threshold: float = 0.35
    
    # Storage
    artifact_storage_path: str = "./artifacts"
    use_mongodb: bool = False
    mongodb_uri: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()