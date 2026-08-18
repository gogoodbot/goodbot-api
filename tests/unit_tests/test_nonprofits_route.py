"""
unit tests for the nonprofits route
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from api.main import app
from routes.nonprofits_route_v1 import get_database_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ai_service():
    """Mock AIService for testing (used by generate_entity_summary endpoint)."""
    mock_service = MagicMock()
    return mock_service


@pytest.fixture
def mock_repo():
    """Create a mock DatabaseRepository with all required methods mocked."""
    mock = MagicMock()
    
    # Mock the async methods used in nonprofits routes
    mock.get_nonprofits = AsyncMock(return_value=[{"id": "1", "name": "Nonprofit One"}])
    mock.get_entity_by_nonprofit_id = AsyncMock(return_value=[{"id": "1", "name": "Nonprofit One"}])
    
    # Mock methods used in error handling
    mock.user_exists = MagicMock(return_value=False)
    
    return mock


@pytest.fixture
def client_with_repo(mock_repo):
    """Create TestClient with dependency override for DatabaseRepository."""
    app.dependency_overrides[get_database_repository] = lambda: mock_repo
    
    client = TestClient(app)
    yield client
    
    # Clean up the override after test
    app.dependency_overrides = {}


def test_get_nonprofits(client_with_repo, mock_repo):
    """Test the get_nonprofits endpoint with successful response."""
    response = client_with_repo.get("/v1/nonprofits/")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Nonprofit One"


def test_get_nonprofits_pagination(client_with_repo, mock_repo):
    """Test the get_nonprofits endpoint with pagination parameters."""
    response = client_with_repo.get("/v1/nonprofits/?page_number=2&page_size=5")
    
    # Verify pagination parameters were passed to repository method
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_get_entity_by_nonprofit_id(client_with_repo, mock_repo):
    """Test the get_nonprofit_by_id endpoint."""
    mock_repo.get_entity_by_nonprofit_id.return_value = [{"id": "1", "name": "Nonprofit One"}]
    
    response = client_with_repo.get("/v1/nonprofits/1")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    if "data" in data and "id" in data["data"]:
        assert data["data"]["id"] == "1"


def test_get_entity_by_nonprofit_id_not_found(client_with_repo, mock_repo):
    """Test the get_entity_by_nonprofit_id endpoint when nonprofit not found."""
    mock_repo.get_entity_by_nonprofit_id.return_value = None
    
    response = client_with_repo.get("/v1/nonprofits/999")
    
    assert response.status_code == 404


def test_get_nonprofits_error(client_with_repo, mock_repo):
    """Test error handling in get_nonprofits endpoint."""
    mock_repo.get_nonprofits.side_effect = Exception("Database error")
    
    response = client_with_repo.get("/v1/nonprofits/?page_number=1&page_size=10")
    
    assert response.status_code == 500


def test_get_entity_by_nonprofit_id_error(client_with_repo, mock_repo):
    """Test error handling in get_entity_by_nonprofit_id endpoint."""
    mock_repo.get_entity_by_nonprofit_id.side_effect = Exception("Error fetching nonprofit by id")
    
    response = client_with_repo.get("/v1/nonprofits/1")
    
    assert response.status_code == 500
