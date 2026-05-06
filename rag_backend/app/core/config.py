from pydantic_settings import BaseSettings, SettingsConfigDict
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

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4"

    # NVIDIA NIM — embeddings via OpenAI-compatible endpoint (DGX Spark / NVIDIA cloud)
    # Set NVIDIA_BASE_URL to your local NIM container, e.g. http://localhost:8000/v1,
    # or leave as the NVIDIA cloud endpoint and supply NVIDIA_API_KEY.
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    # Chat / generation model served by the NIM container or NVIDIA cloud
    NVIDIA_CHAT_MODEL: str = "meta/llama-3.3-70b-instruct"
    # Embeddings model
    NVIDIA_EMBED_MODEL: str = "nvidia/llama-nemotron-embed-1b-v2"
    # input_type for passage (document) embedding — "passage" or "query"
    NVIDIA_EMBED_INPUT_TYPE_PASSAGE: str = "passage"
    NVIDIA_EMBED_INPUT_TYPE_QUERY: str = "query"
    NVIDIA_EMBED_TRUNCATE: str = "NONE"

    # Google Drive-backed knowledge base (primary source for ingestion)
    GOOGLE_DRIVE_FOLDER_URL: str = (
        "https://drive.google.com/drive/folders/"
        "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP?usp=drive_link"
    )
    GOOGLE_DRIVE_FOLDER_ID: str = "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP"
    GOOGLE_DRIVE_API_KEY: str = ""
    GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE: str = ""
    GOOGLE_DRIVE_CHUNK_SIZE: int = 1200
    GOOGLE_DRIVE_MAX_FILES: int = 200

    # YouTube-backed knowledge ingestion source
    YOUTUBE_CHANNEL: str = ""
    YOUTUBE_MAX_VIDEOS: int = 25
    YOUTUBE_CHUNK_SIZE: int = 1200

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

settings = Settings()
