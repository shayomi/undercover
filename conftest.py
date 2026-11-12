import pytest
from fastapi.testclient import TestClient

from backend.db import seed
from backend.main import app


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    """Give every test a fresh database of its own."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "undercover.db"))
    seed()


@pytest.fixture
def client():
    return TestClient(app)
