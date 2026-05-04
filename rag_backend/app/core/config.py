from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Legacy Hugging Face settings are disabled; all generation routes through LM Studio.
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = "lmstudio"
    LLM_MODEL_NAME: str = "google/gemma-4-E4B-it"
    HF_API_BASE: str = "https://api-inference.huggingface.co"

    # Infrastructure
    VECTOR_DB_URL: str = ""
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    CORS_ORIGINS: List[str] = []

    # LM Studio (active provider via the OpenAI-compatible HTTP endpoint)
    LM_STUDIO_BASE_URL: str = "http://localhost:1234"
    LM_STUDIO_MCP_URL: str = "http://localhost:1234/mcp"
    LM_STUDIO_MODEL: str = "google/gemma-4-E4B-it"
    LM_STUDIO_USE_MCP: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
