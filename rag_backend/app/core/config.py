from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

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

    # Google Drive-backed knowledge base (primary source for ingestion)
    GOOGLE_DRIVE_FOLDER_URL: str = (
        "https://drive.google.com/drive/folders/"
        "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP?usp=drive_link"
    )
    GOOGLE_DRIVE_FOLDER_ID: str = "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP"
    GOOGLE_DRIVE_API_KEY: str = ""
    GOOGLE_DRIVE_CHUNK_SIZE: int = 1200
    GOOGLE_DRIVE_MAX_FILES: int = 200

    class Config:
        env_file = str(ENV_FILE)
        extra = "ignore"

settings = Settings()
