"""
database operations unit tests
"""

from unittest.mock import MagicMock
import pytest
from app.routes.database import user_exists, get_user_by_username, insert_user, get_litigations


@pytest.fixture
def mock_client(mocker):
    """
    mock the client object
    """
    # mock the client.table().select().execute() chain
    mock_db_client = mocker.patch("app.routes.database.client", autospec=True)
    return mock_db_client


def test_user_exists(mock_client):
    """
    test user_exists function
    """
    # mock response for a user that exists and is active
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[{"username": "testuser", "active": 1}])

    result = user_exists("testuser")
    assert result is True

    # mock response for a user that doesn't exist
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[])
    result = user_exists("nonexistentuser")
    assert result is False


def test_get_user_by_username(mock_client):
    """
    test get_user_by_username function
    """
    # mock response for a valid user
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(
            data=[{"username": "testuser", "password": "hashed_password"}])

    result = get_user_by_username("testuser")
    assert result == {"username": "testuser", "password": "hashed_password"}

    # mock response for a nonexistent user
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[])
    result = get_user_by_username("nonexistentuser")
    assert result is None


def test_insert_user(mock_client):
    """
    test insert_user function
    """
    # mock response for a successful insertion
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data={"username": "testuser", "password": "hashed_password"}
    )

    result = insert_user("testuser", "hashed_password")
    assert result == {"username": "testuser", "password": "hashed_password"}

    # mock response for a failed insertion
    mock_client.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Insertion failed")
    result = insert_user("testuser", "hashed_password")
    assert result is None


def test_get_litigations(mock_client):
    """
    test get_litigations function
    """
    # mock response for litigations
    mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[{"id": 1, "case_name": "Litigation A"},
              {"id": 2, "case_name": "Litigation B"}]
    )

    result = get_litigations()
    assert result == [{"id": 1, "case_name": "Litigation A"}, {
        "id": 2, "case_name": "Litigation B"}]

    # mock response for an empty database
    mock_client.table.return_value.select.return_value.execute.return_value = \
        MagicMock(data=[])
    result = get_litigations()
    assert result == []

    # Mock response for a database error
    mock_client.table.return_value.select.return_value.execute.side_effect = Exception(
        "Database error")
    result = get_litigations()
    assert result is None
