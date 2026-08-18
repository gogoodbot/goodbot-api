import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from routes.experts_route_v1 import get_database_repository

@pytest.fixture
def mock_repo():
    # Create a mock object that can handle both sync and async methods
    mock = MagicMock()
    # Explicitly make the async methods AsyncMocks
    mock.get_experts = AsyncMock()
    mock.get_expert_by_id = AsyncMock()
    return mock

@pytest.fixture
def client(mock_repo):
    # Set up the dependency override
    app.dependency_overrides[get_database_repository] = lambda: mock_repo
    client = TestClient(app)
    yield client
    # Clean up overrides after the test
    app.dependency_overrides = {}

def test_get_experts_success(client, mock_repo):
    mock_repo.get_experts.return_value = [{"id": 1, "name": "Expert 1"}]
    
    response = client.get("/v1/experts")
    
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["name"] == "Expert 1"

def test_get_expert_by_id_success(client, mock_repo):
    mock_repo.get_expert_by_id.return_value = {"id": 1, "name": "Expert 1"}
    
    response = client.get("/v1/experts/1")
    
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Expert 1"

def test_get_experts_error(client, mock_repo):
    mock_repo.get_experts.side_effect = Exception("Database Error")
    
    response = client.get("/v1/experts")
    
    assert response.status_code == 500

def test_get_expert_by_id_not_found(client, mock_repo):
    mock_repo.get_expert_by_id.return_value = None
    
    response = client.get("/v1/experts/999")
    
    assert response.status_code == 404
