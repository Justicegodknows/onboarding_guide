from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    LLM_API_KEY: str
    VECTOR_DB_URL: str
    DATABASE_URL: str
    CORS_ORIGINS: List[str] = []

    class Config:
        env_file = ".env"

settings = Settings()
