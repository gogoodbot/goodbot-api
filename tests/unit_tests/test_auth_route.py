"""
auth route unit tests
"""
import os
from dotenv import load_dotenv
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app  # Replace with your FastAPI app import
from api.routes.auth_route_v1 import create_access_token, verify_access_token

load_dotenv()


client = TestClient(app)


def test_login_success(mocker):
    """
    Mock database responses
    """
    mocker.patch("api.routes.auth_route_v1.DatabaseRepository.user_exists", return_value=True)
    mocker.patch("api.routes.auth_route_v1.DatabaseRepository.get_user_by_username", return_value={
                 "password": bcrypt.hashpw(b"test", bcrypt.gensalt()).decode()})

    response = client.post(
        "/v1/login/",
        data={"username": "testuser", "password": "test"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_failure_invalid_credentials(mocker):
    """
    test login failure with invalid credentials
    """
    mocker.patch("api.routes.auth_route_v1.DatabaseRepository.user_exists", return_value=False)

    response = client.post(
        "/v1/login",
        data={"username": "invaliduser", "password": "invalid"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


async def test_create_access_token():
    """
    test create access token
    """
    data = {"sub": "testuser"}
    token = create_access_token(data)
    decoded_token = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=[
                               os.environ.get("ALGORITHM")])
    assert decoded_token["sub"] == "testuser"


@pytest.mark.asyncio
async def test_verify_access_token_valid(mocker):
    """
    test verify access token
    """
    mocker.patch("api.routes.auth_route_v1.jwt.decode",
                 return_value={"sub": "testuser"})
    payload = await verify_access_token("testtoken")
    assert payload["sub"] == "testuser"


@pytest.mark.asyncio
async def test_verify_access_token_invalid(mocker):
    """
    test verify access token with invalid token
    """
    mocker.patch("api.routes.auth_route_v1.jwt.decode",
                 side_effect=InvalidTokenError)
    with pytest.raises(HTTPException) as excinfo:
        await verify_access_token("invalid.token")
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"
