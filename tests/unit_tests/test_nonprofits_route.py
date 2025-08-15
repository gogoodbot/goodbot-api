"""
unit tests for the nonprofits route
"""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, AsyncMock
from api.main import app
from data.database_repository import DatabaseRepository

client = TestClient(app)

@pytest.fixture
def mock_database_repository():
    """
    Mock DatabaseRepository for testing.
    """
    mock_repo = MagicMock(spec=DatabaseRepository)
    mock_repo.get_experts = AsyncMock()
    mock_repo.get_expert_by_id = AsyncMock()
    return mock_repo

def test_get_nonprofits(mocker):
    """
    Test the get_nonprofits endpoint.
    """
    mock_nonprofits = [
        {"id": "1", "name": "Nonprofit One"}, 
        {"id": "2", "name": "Nonprofit Two"}
    ]
    mocker.patch(
        "routes.nonprofits_route_v1.DatabaseRepository.get_nonprofits",
        return_value=mock_nonprofits
    )

    response = client.get("/v1/nonprofits/")
    assert response.status_code == 200
    assert response.json() == {"data": mock_nonprofits}

def test_get_entity_by_nonprofit_id(mocker):
    """
    Test the get_entity_by_nonprofit_id endpoint.
    """
    mock_nonprofit = {"id": "1", "name": "Nonprofit One"}
    mocker.patch(
        "routes.nonprofits_route_v1.DatabaseRepository.get_entity_by_nonprofit_id",
        return_value=mock_nonprofit
    )

    response = client.get("/v1/nonprofits/1")
    assert response.status_code == 200
    assert response.json() == {"data": {"id": "1", "name": "Nonprofit One"}}

def test_get_nonprofits_error(mocker):
    """
    Test error handling in get_nonprofits endpoint.
    """
    # Mock an exception in the repository method
    mocker.patch(
        "routes.nonprofits_route_v1.DatabaseRepository.get_nonprofits",
        side_effect=Exception("Database error")
    )

    response = client.get("/v1/nonprofits/?page_number=1&page_size=10")
    assert response.status_code == 200
    assert response.json() == {"message": "Error fetching paged nonprofits"}

def test_get_entity_by_nonprofit_id_error(mocker):
    """
    Test error handling in get_entity_by_nonprofit_id endpoint.
    """
    mocker.patch(
        "routes.nonprofits_route_v1.DatabaseRepository.get_entity_by_nonprofit_id",
        side_effect=Exception("Error fetching nonprofit by id")
    )

    response = client.get("/v1/nonprofits/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Error fetching nonprofit by id"}
