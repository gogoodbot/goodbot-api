"""
unit tests for the AuthMiddleware class
"""

from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from api.routes.middleware import AuthMiddleware


@pytest.fixture
def app(mocker):
    """
    mock the verify_access_token function
    """
    # mock verify_access_token
    mocker.patch(
        "api.routes.middleware.verify_access_token",
        new_callable=AsyncMock
    )

    # create a FastAPI app with the middleware applied
    fastapi_app = FastAPI()

    @fastapi_app.get("/v1/test-endpoint")
    async def test_endpoint():
        return JSONResponse(content={"message": "Success"}, status_code=200)

    fastapi_app.add_middleware(AuthMiddleware)
    return fastapi_app


@pytest.fixture
def client(app):
    """
    create test client
    """
    return TestClient(app)


def test_request_without_auth_header(client):
    """
    test a request without the Authorization header.
    """
    response = client.get("/v1/test-endpoint")
    assert response.status_code == 200
    assert response.json() == {"message": "Success"}


def test_request_with_valid_token(client, mocker):
    """
    test a request with a valid Authorization token.
    """
    # mock verify_access_token to return valid payload
    mock_verify = mocker.patch(
        "api.routes.middleware.verify_access_token", new_callable=AsyncMock)
    mock_verify.return_value = {"sub": "testuser"}

    # perform request with a valid token
    response = client.get(
        "/v1/test-endpoint", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 200
    assert response.json() == {"message": "Success"}

    # assert the mocked verify_access_token was called
    mock_verify.assert_called_once_with("valid-token")


def test_request_with_invalid_token(client, mocker):
    """
    test a request with an invalid Authorization token.
    """
    # mock verify_access_token to raise HTTPException
    mock_verify = mocker.patch(
        "api.routes.middleware.verify_access_token", new_callable=AsyncMock)
    mock_verify.side_effect = HTTPException(
        status_code=401, detail="Invalid token")

    # perform request with an invalid token
    response = client.get(
        "/v1/test-endpoint", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}

    # assert the mocked verify_access_token was called
    mock_verify.assert_called_once_with("invalid-token")


def test_request_with_malformed_token(client, mocker):
    """
    test a request with a malformed Authorization header.
    """
    # mock verify_access_token to ensure it's not called
    mock_verify = mocker.patch(
        "api.routes.middleware.verify_access_token", new_callable=AsyncMock)

    # perform request with a malformed Authorization header
    response = client.get(
        "/v1/test-endpoint", headers={"Authorization": "MalformedToken"})
    assert response.status_code == 500
    assert response.json()["detail"].startswith("Error:")

    # ensure verify_access_token was not called
    mock_verify.assert_not_called()
