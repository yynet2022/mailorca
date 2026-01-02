import pytest
from fastapi.testclient import TestClient

from mailorca.web import app
from mailorca.store import STORE

@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_store():
    """Clear the in-memory store before each test."""
    STORE.mails.clear()
    yield
    STORE.mails.clear()
