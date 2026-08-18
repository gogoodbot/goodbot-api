import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api.main import app
from routes.users_route_v1 import get_database_repository, verify_access_token

@pytest.fixture
def mock_repo():
    mock = MagicMock()
    # These are sync methods in DatabaseRepository
    mock.user_exists = Magicmock() # wait, typo here, should be MagicMock
    return mock

@pytest.fixture
def mock_repo_fixed():
    mock = MagicMock()
    # These are sync methods in DatabaseRepository
    mock.user_exists = MagicMock()
    mock.get_user_by_username = MagicMock()
    mock.insert_user = MagicMock()
    return mock

@pytest.fixture
def mock_auth_token():
    # This will return the decoded payload
    return {"sub": "testuser@example.com"}

@pytest.fixture
def client(mock_repo_fixed, mock_auth_token):
    # Override database repository
    app.dependency_overrides[get_database_repository] = lambda: mock_repo_fixed
    # Override authentication dependency
    app.dependency_overrides[verify_access_token] = lambda: mock_auth_token
    
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

def test_create_user_success(client, mock_repo_fixed):
    # Setup mock
    mock_repo_fixed.user_exists.return_value = False
    mock_repo_fixed.insert_user.return_value = [{"username": "testuser@example.com"}]
    
    # Payload for CreateUserRequest (must match validation rules in CreateUserRequest)
    # email pattern: r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    user_data = {
        "username": "testuser@example.com", 
        "password": "Password123"
    }
    
    response = client.post("/v1/users", json=user_data)
    
    assert response.status_code == 201
    assert response.json()["username"] == "testuser@example.com"
    mock_repo_fixed.insert_user.assert_called_once()

def test_create_user_already_exists(client, mock_repo_fixed):
    # Setup mock
    mock_repo_fixed.user_exists.return_value = True
    
    user_data = {
        "username": "testuser@example.com", 
        "password": "Password123"
    }
    
    response = client.post("/v1/users", json=user_data)
    
    assert response.status_code == 409
    assert response.json()["detail"] == "User already exists"

def test_get_user_me_success(client, mock_repo_fixed):
    # Setup mock
    mock_repo_fixed.get_user_by_username.return_value = {"username": "testuser@example.com", "active": 1}
    
    response = client.get("/v1/users/me")
    
    assert response.status_code == 200
    assert response.json()["username"] == "testuser@example.com"
    assert response.json()["active"] == 1

def test_get_user_me_not_found(client, mock_repo_fixed):
    # Setup mock
    mock_repo_fixed.get_user_by_username.return_value = None
    
    response = client.get("/v1/users/me")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
