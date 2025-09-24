"""
unit tests for the search route
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

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


def test_search(mocker):
    """
    Test the search endpoint.
    """
    mock_search_results = [
        {"id": "1", "name": "Result One"},
        {"id": "2", "name": "Result Two"},
    ]
    mocker.patch(
        "routes.search_route_v1.DatabaseRepository.search_by_keywords",
        return_value=mock_search_results,
    )

    response = client.get("/v1/search/testquery")
    assert response.status_code == 200
    assert response.json() == mock_search_results


def test_search_no_results(mocker):
    """
    Test the search endpoint with no results.
    """
    mocker.patch(
        "routes.search_route_v1.DatabaseRepository.search_by_keywords",
        return_value=None,
    )

    response = client.get("/v1/search/emptyquery")
    assert response.status_code == 200
    assert response.json() == {"message": "No homepage data found"}


def test_search_error(mocker):
    """
    Test error handling in search endpoint.
    """
    # Mock an exception in the repository method
    mocker.patch(
        "routes.search_route_v1.DatabaseRepository.search_by_keywords",
        side_effect=Exception("Database error"),
    )

    response = client.get("/v1/search/errorquery")
    assert response.status_code == 200
    assert response.json() == {"message": 'Error while searching for "{query}"'}
