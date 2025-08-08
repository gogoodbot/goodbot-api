"""
litigations route unit tests
"""

import os
import datetime
import pytest
import jwt
from fastapi.testclient import TestClient
from fastapi import HTTPException
from api.main import app

client = TestClient(app)


@pytest.fixture
def mock_dependencies(mocker):
    """
    Mock external dependencies for litigations route.
    """
    mocker.patch(
        "api.routes.litigations_route_v1.verify_access_token",
        return_value={"sub": "testuser"}
    )
    mocker.patch("api.routes.litigations_route_v1.DatabaseRepository.get_litigations")


def test_fetch_litigations_valid_token(mock_dependencies, mocker):
    """
    test fetching litigations with a valid token.
    """
    # mock environment variables
    mocker.patch.dict(
        os.environ, {"SECRET_KEY": "testsecret", "ALGORITHM": "HS256"}
    )

    # create a valid JWT for testing
    secret_key = "testsecret"
    algorithm = "HS256"
    payload = {"sub": "testuser", "exp": datetime.datetime.now(datetime.UTC) +
               datetime.timedelta(minutes=5)}
    valid_token = jwt.encode(payload, secret_key, algorithm=algorithm)

    # mock verify_access_token to simulate valid token
    mocker.patch(
        "api.routes.litigations_route_v1.verify_access_token",
        return_value=payload
    )

    # mock get_litigations to return dummy data
    mock_litigations = [{"id": 1, "case_name": "Test Case"}]
    mocker.patch("api.routes.litigations_route_v1.DatabaseRepository.get_litigations",
                 return_value=mock_litigations)

    # perform request
    response = client.get(
        "/v1/litigations/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )

    assert response.status_code == 200
    assert response.json() == {"data": mock_litigations}


def test_fetch_litigations_invalid_token(mock_dependencies, mocker):
    """
    test fetching litigations with an invalid token.
    """
    # patch verify_access_token in the middleware
    mocker.patch(
        "api.routes.middleware.verify_access_token",
        side_effect=HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
    )

    # perform request with invalid token
    response = client.get(
        "/v1/litigations/",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_fetch_litigations_db_error(mock_dependencies, mocker):
    """
    Test fetching litigations with a database error.
    """
    # mock environment variables
    mocker.patch.dict(
        os.environ, {"SECRET_KEY": "testsecret", "ALGORITHM": "HS256"}
    )

    # create a valid JWT for testing
    secret_key = "testsecret"
    algorithm = "HS256"
    payload = {"sub": "testuser", "exp": datetime.datetime.now(datetime.UTC) +
               datetime.timedelta(minutes=5)}
    valid_token = jwt.encode(payload, secret_key, algorithm=algorithm)

    # mock verify_access_token to simulate valid token
    mocker.patch(
        "api.routes.litigations_route_v1.verify_access_token",
        return_value=valid_token
    )

    # mock get_litigations to raise an exception
    mocker.patch(
        "api.routes.litigations_route_v1.DatabaseRepository.get_litigations",
        side_effect=Exception("Database error")
    )

    # perform request
    response = client.get(
        "/v1/litigations/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )

    assert response.status_code == 200  # route handles exceptions gracefully
    assert response.json() == {"message": "Error fetching litigations"}
