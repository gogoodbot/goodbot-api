"""
users route unit tests
"""

import os
from datetime import datetime, timedelta
import pytest
import jwt
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_dependencies(mocker):
    """
    mocking the functions that interact with the database
    """
    mocker.patch("app.routes.users_route_v1.user_exists", return_value=False)
    mocker.patch("app.routes.users_route_v1.insert_user", return_value=True)
    mocker.patch(
        "app.routes.users_route_v1.get_user_by_username",
        return_value={"username": "testuser",
                      "password": "hashed_pw",
                      "active": 1}
    )

    # simulate a valid token
    mocker.patch(
        "app.routes.auth_route_v1.verify_access_token",
        return_value={"sub": "testuser"}
    )


def test_create_user(mock_dependencies):
    """
    test user creation with valid data.
    """
    user_data = {"username": "testuser", "password": "password123"}

    response = client.post("/users/", json=user_data)

    assert response.status_code == 200
    assert response.json() == {"message": "User created successfully"}


def test_create_user_already_exists(mock_dependencies, mocker):
    """
    Test user creation when the user already exists.
    """
    # mock `user_exists` to simulate the user already exists
    mocker.patch("app.routes.users_route_v1.user_exists", return_value=True)

    user_data = {"username": "existinguser", "password": "password123"}

    response = client.post("/users/", json=user_data)

    assert response.status_code == 200
    assert response.json() == {"message": "User already exists"}


def test_get_user(mock_dependencies, mocker):
    """
    test fetching the user info using a valid access token.
    """
    # mock environment variables
    mocker.patch.dict(
        os.environ, {"SECRET_KEY": "testsecret", "ALGORITHM": "HS256"}
    )

    # create a valid JWT for testing
    secret_key = "testsecret"
    algorithm = "HS256"
    payload = {"sub": "testuser", "exp": datetime.utcnow() +
               timedelta(minutes=5)}
    valid_token = jwt.encode(payload, secret_key, algorithm=algorithm)

    # patch the verify_access_token function to return a valid payload
    mocker.patch(
        "app.routes.users_route_v1.verify_access_token",
        return_value=payload
    )

    # perform the request with the valid token
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {valid_token}"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_get_user_invalid_token(mock_dependencies, mocker):
    """
    test fetching user info with an invalid token (simulate no user found).
    """
    # patch verify_access_token in the middleware
    mocker.patch(
        "app.routes.middleware.verify_access_token",
        side_effect=HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
    )

    # perform the request with an invalid token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_test_route(mock_dependencies):
    """
    test the public route that doesn't require authentication.
    """
    response = client.get("/users/test")

    assert response.status_code == 200
    assert response.json() == {"success": "public api"}
