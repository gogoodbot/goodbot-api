"""
unit test class for experts route
"""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, AsyncMock
from api.main import app
from api.routes.database import DatabaseRepository

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

def test_get_experts(mocker):
    """
    Test the get_experts endpoint.
    """
    mock_experts = [
        {"id": "1", "name": "Expert One"}, 
        {"id": "2", "name": "Expert Two"}
    ]
    mocker.patch(
        "api.routes.experts_route_v1.DatabaseRepository.get_experts",
        return_value=mock_experts
    )

    response = client.get("/v1/experts/")
    assert response.status_code == 200
    assert response.json() == {"data": mock_experts}

def test_get_expert_by_id(mocker):
    """
    Test the get_expert_by_id endpoint.
    """
    mock_expert = {"id": "1", "name": "Expert One"}
    mocker.patch(
        "api.routes.experts_route_v1.DatabaseRepository.get_expert_by_id",
        return_value=mock_expert
    )

    response = client.get("/v1/experts/1")
    assert response.status_code == 200
    assert response.json() == {"data": {"id": "1", "name": "Expert One"}}

def test_get_experts_error(mocker):
    """
    Test error handling in get_experts endpoint.
    """
    # Mock an exception in the repository method
    mocker.patch(
        "api.routes.experts_route_v1.DatabaseRepository.get_experts",
        side_effect=Exception("Database error")
    )

    response = client.get("/v1/experts/?page_number=1&page_size=10")
    assert response.status_code == 200
    assert response.json() == {"message": "Error fetching paged experts"}

def test_get_expert_by_id_error(mocker):
    """
    Test error handling in get_expert_by_id endpoint.
    """
    mocker.patch(
        "api.routes.experts_route_v1.DatabaseRepository.get_expert_by_id",
        side_effect=Exception("Error fetching expert by id")
    )

    response = client.get("/v1/experts/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Error fetching expert by id"}
