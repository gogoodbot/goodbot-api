"""
home route unit tests
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from api.main import app
from routes.home_route_v1 import get_homepage_data
from data.database_repository import DatabaseRepository
from usecase.get_homepage_data import GetHomePageData

client = TestClient(app)


@pytest.fixture
def mock_database_repository():
    """
    Mock DatabaseRepository for testing
    """
    mock_repo = MagicMock(spec=DatabaseRepository)
    mock_repo.get_structural_subfactors = AsyncMock()
    mock_repo.get_harm_and_risk_by_subfactor_id = AsyncMock()
    mock_repo.get_nonprofits_by_harm_risk_id = AsyncMock()
    mock_repo.get_entity_by_nonprofit_id = AsyncMock()
    return mock_repo

@pytest.fixture
def mock_usecase():
    """
    Mock GetHomePageData use case for testing
    """
    mock_usecase = MagicMock(spec=GetHomePageData)
    mock_usecase.execute = AsyncMock()
    return mock_usecase

def test_get_home_page_data(mocker, mock_database_repository, mock_usecase):
    """
    Test get_homepage_data dependency function
    """
    mocker.patch(
        "routes.home_route_v1.get_database_repository",
        return_value=mock_database_repository
    )
    mocker.patch(
        "routes.home_route_v1.GetHomePageData",
        return_value=mock_usecase
    )

    result = get_homepage_data()
    assert result == mock_usecase

def test_home_page_data_error(mocker, mock_database_repository, mock_usecase):
    """
    Test error handling in get_homepage_data
    """

    mock_usecase.execute = AsyncMock(side_effect=Exception("Database error"))

    mocker.patch("routes.home_route_v1.get_database_repository", return_value=mock_database_repository)
    mocker.patch("routes.home_route_v1.GetHomePageData", return_value=mock_usecase)

    response = client.get("/v1/home")
    assert response.status_code == 200
    assert response.json()["message"] == "Error fetching homepage data"
