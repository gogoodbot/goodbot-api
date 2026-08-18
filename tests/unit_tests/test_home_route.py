import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from api.main import app
from routes.home_route_v1 import get_database_repository

@pytest.fixture
def mock_repo():
    mock = MagicMock()
     # Mock the async method for get_page_data in usecase
    mock.get_homepage_data = AsyncMock(return_value=[])
    return mock

@pytest.fixture
def client(mock_repo):
     # Override the database repository dependency
    app.dependency_overrides[get_database_repository] = lambda: mock_repo
    
    client = TestClient(app)
    yield client
    
     # Clean up overrides after test
    app.dependency_overrides = {}

def test_get_home_page_data(client, mock_repo):
     # Setup mock
    pass  # Already set up in the fixture above
    
    response = client.get("/v1/home")
    
    assert response.status_code == 200
    assert response.json()["subfactors"] == []

def test_get_home_page_data_error(client, mock_repo):
     # Setup mock to raise an exception on get_homepage_data
    mock_repo.get_homepage_data = AsyncMock(side_effect=Exception("Error"))
    
    response = client.get("/v1/home")
    
    assert response.status_code == 500
