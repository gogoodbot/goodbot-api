"""
database operations unit tests
"""

from unittest.mock import MagicMock
import pytest
from api.routes.database import DatabaseRepository

@pytest.fixture
def mock_client(mocker):
    """
    mock the client object
    """
    # mock the client.table().select().execute() chain
    mock_db_client = MagicMock()
    mocker.patch("api.routes.database.get_database_client", return_value=mock_db_client)
    return mock_db_client

@pytest.fixture
def repository(mock_client):
    """
    fixture to create a DatabaseRepository instance with the mocked client
    """
    return DatabaseRepository()

def test_user_exists(mock_client, repository):
    """
    test user_exists function
    """
    # mock response for a user that exists and is active
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[{"username": "testuser", "active": 1}])

    result = repository.user_exists("testuser")
    assert result is True

    # mock response for a user that doesn't exist
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[])
    result = repository.user_exists("nonexistentuser")
    assert result is False


def test_get_user_by_username(mock_client, repository):
    """
    test get_user_by_username function
    """
    # mock response for a valid user
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(
            data=[{"username": "testuser", "password": "hashed_password"}])

    result = repository.get_user_by_username("testuser")
    assert result == {"username": "testuser", "password": "hashed_password"}

    # mock response for a nonexistent user
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[])
    result = repository.get_user_by_username("nonexistentuser")
    assert result is None


def test_insert_user(mock_client, repository):
    """
    test insert_user function
    """
    # mock response for a successful insertion
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data={"username": "testuser", "password": "hashed_password"}
    )

    result = repository.insert_user("testuser", "hashed_password")
    assert result == {"username": "testuser", "password": "hashed_password"}

    # mock response for a failed insertion
    mock_client.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Insertion failed")
    result = repository.insert_user("testuser", "hashed_password")
    assert result is None


def test_get_litigations(mock_client, repository):
    """
    test get_litigations function
    """
    # mock response for litigations
    mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[{"id": 1, "case_name": "Litigation A"},
              {"id": 2, "case_name": "Litigation B"}]
    )

    result = repository.get_litigations()
    assert result == [{"id": 1, "case_name": "Litigation A"}, {
        "id": 2, "case_name": "Litigation B"}]

    # mock response for an empty database
    mock_client.table.return_value.select.return_value.execute.return_value = \
        MagicMock(data=[])
    result = repository.get_litigations()
    assert result == []

    # mock response for a database error
    mock_client.table.return_value.select.return_value.execute.side_effect = Exception(
        "Database error")
    result = repository.get_litigations()
    assert result is None

@pytest.mark.asyncio
async def test_get_experts(mock_client, repository):
    """
    test get_experts function
    """
    # mock response for experts
    mock_client.table.return_value.select.return_value.range.return_value.execute.return_value = \
        MagicMock(data=[{"id": 1, "name": "Expert A"}, {"id": 2, "name": "Expert B"}])

    result = await repository.get_experts(page_number=1, page_size=10)
    assert sorted(result, key=lambda d: d["id"]) == sorted([{"id": 1, "name": "Expert A"}, {"id": 2, "name": "Expert B"}], key=lambda d: d["id"])

    # mock response for an empty database
    mock_client.table.return_value.select.return_value.range.return_value.execute.return_value = \
        MagicMock(data=[])
    result = await repository.get_experts(page_number=1, page_size=10)
    assert result == []

    # mock response for a database error
    mock_client.table.return_value.select.return_value.range.return_value.execute.side_effect = Exception(
        "Database error")
    result = await repository.get_experts(page_number=1, page_size=10)
    assert result is None

@pytest.mark.asyncio
async def test_get_expert_by_id(mock_client, repository):
    """
    test get_expert_by_id function
    """
    # mock response for a valid expert
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data={"id": "expert1", "name": "Expert One"})

    result = await repository.get_expert_by_id("expert1")
    assert result == {"id": "expert1", "name": "Expert One"}

    # mock response for a nonexistent expert
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[])
    result = await repository.get_expert_by_id("nonexistent_expert")
    assert len(result) == 0

    # mock response for a database error
    mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception(
        "Database error")
    result = await repository.get_expert_by_id("expert1")
    assert result is None
