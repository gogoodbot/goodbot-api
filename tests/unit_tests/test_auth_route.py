from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import bcrypt
import jwt
import pytest
from fastapi import HTTPException

from routes import auth_route_v1


class TestGetDatabaseRepository:
    def test_returns_database_repository(self):
        with patch("routes.auth_route_v1.DatabaseRepository") as mock_repository:
            result = auth_route_v1.get_database_repository()

            mock_repository.assert_called_once()
            assert result == mock_repository.return_value


class TestAuthenticateUser:
    def test_authenticates_valid_user(self):
        repository = MagicMock()
        password = "password123"
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        repository.get_user_by_username.return_value = {
            "username": "testuser",
            "password": hashed_password,
        }

        result = auth_route_v1.authenticate_user("testuser", password, repository)

        assert result is True
        repository.get_user_by_username.assert_called_once_with(username="testuser")

    def test_returns_false_when_user_does_not_exist(self):
        repository = MagicMock()
        repository.get_user_by_username.return_value = None

        result = auth_route_v1.authenticate_user("testuser", "password", repository)

        assert result is False

    def test_returns_false_for_invalid_password(self):
        repository = MagicMock()
        repository.get_user_by_username.return_value = {
            "username": "testuser",
            "password": bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode(),
        }

        result = auth_route_v1.authenticate_user(
            "testuser", "wrong-password", repository
        )

        assert result is False

    def test_returns_false_when_repository_raises_exception(self):
        repository = MagicMock()
        repository.get_user_by_username.side_effect = Exception("DB error")

        result = auth_route_v1.authenticate_user("testuser", "password", repository)

        assert result is False


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        repository = MagicMock()
        repository.user_exists.return_value = False

        form_data = SimpleNamespace(
            username="testuser",
            password="password",
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_route_v1.login(form_data, repository)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid username or password"
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        repository = MagicMock()
        repository.user_exists.return_value = True

        with patch("routes.auth_route_v1.authenticate_user", return_value=False):
            form_data = SimpleNamespace(
                username="testuser",
                password="wrong-password",
            )

            with pytest.raises(HTTPException) as exc_info:
                await auth_route_v1.login(form_data, repository)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect username or password"

    @pytest.mark.asyncio
    async def test_login_success(self):
        repository = MagicMock()
        repository.user_exists.return_value = True

        form_data = SimpleNamespace(
            username="testuser",
            password="password",
        )

        with patch("routes.auth_route_v1.authenticate_user", return_value=True), patch(
            "routes.auth_route_v1.create_access_token",
            return_value="test-token",
        ):
            result = await auth_route_v1.login(form_data, repository)

        assert result.access_token == "test-token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_token_creation_failure(self):
        repository = MagicMock()
        repository.user_exists.return_value = True

        form_data = SimpleNamespace(
            username="testuser",
            password="password",
        )

        with patch("routes.auth_route_v1.authenticate_user", return_value=True), patch(
            "routes.auth_route_v1.create_access_token",
            side_effect=Exception("JWT error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_route_v1.login(form_data, repository)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Failed to create access token"


class TestCreateAccessToken:
    def test_creates_token_with_expiration(self):
        expires_delta = timedelta(minutes=10)
        data = {"sub": "testuser"}

        token = auth_route_v1.create_access_token(data, expires_delta)

        payload = jwt.decode(
            token,
            auth_route_v1.settings.secret_key,
            algorithms=[auth_route_v1.settings.algorithm],
        )

        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_creates_token_with_default_expiration(self):
        data = {"sub": "testuser"}

        token = auth_route_v1.create_access_token(data)

        payload = jwt.decode(
            token,
            auth_route_v1.settings.secret_key,
            algorithms=[auth_route_v1.settings.algorithm],
        )

        assert payload["sub"] == "testuser"
        assert "exp" in payload


class TestVerifyAccessToken:
    @pytest.mark.asyncio
    async def test_returns_payload_for_valid_token(self):
        token = auth_route_v1.create_access_token(
            {"sub": "testuser"},
            timedelta(minutes=10),
        )

        result = await auth_route_v1.verify_access_token(token)

        assert result["sub"] == "testuser"
        assert "exp" in result

    @pytest.mark.asyncio
    async def test_rejects_token_without_username(self):
        token = auth_route_v1.create_access_token(
            {"some_claim": "value"},
            timedelta(minutes=10),
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_route_v1.verify_access_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_rejects_expired_token(self):
        token = auth_route_v1.create_access_token(
            {"sub": "testuser"},
            timedelta(seconds=-1),
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_route_v1.verify_access_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token has expired"

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self):
        with pytest.raises(HTTPException) as exc_info:
            await auth_route_v1.verify_access_token("invalid-token")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self):
        with patch(
            "routes.auth_route_v1.jwt.decode",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_route_v1.verify_access_token("some-token")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
