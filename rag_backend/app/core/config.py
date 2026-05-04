from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # HuggingFace / general LLM (local transformers fallback)
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = "lmstudio"   # lmstudio | huggingface
    LLM_MODEL_NAME: str = "google/gemma-4-E4B-it"
    HF_API_BASE: str = "https://api-inference.huggingface.co"

    # Infrastructure
    VECTOR_DB_URL: str = ""
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    CORS_ORIGINS: List[str] = []

    # LM Studio (primary provider)
    LM_STUDIO_BASE_URL: str = "http://localhost:1234"
    LM_STUDIO_MCP_URL: str = "http://localhost:1234/mcp"
    LM_STUDIO_MODEL: str = "google/gemma-4-E4B-it"
    LM_STUDIO_USE_MCP: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
