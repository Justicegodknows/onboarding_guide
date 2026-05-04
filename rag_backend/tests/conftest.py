"""Shared pytest fixtures for the RAG backend test suite."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous HTTPX test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c
