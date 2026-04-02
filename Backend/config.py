import os
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-haiku-4-5"  
    tavily_api_key: str 
    max_tokens: int = 4096
    faiss_index_path: str = "./faiss_data"

    model_config = SettingsConfigDict(env_file=".env",extra="ignore")


settings = Settings()
