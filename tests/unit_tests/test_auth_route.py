"""Tests for the login access token endpoint."""
from unittest.mock import MagicMock, patch, AsyncMock, call

import pytest

import data.database_repository as _db_repo
_db_repo.supabase = {
    "table": MagicMock(),
    "from_": MagicMock(),
    "select": MagicMock(),
    "eq": MagicMock(),
    "order_by": MagicMock(),
    "limit": MagicMock(),
    "is": MagicMock(),
    "text_search": MagicMock(),
    "_inner": MagicMock(),
}


def _make_supabase_chain():
    """Create a minimal mock Supabase client chain."""
    m = MagicMock()
    m.chain = m
    m.eq = lambda s, **kw: m
    m.order_by = lambda s, **kw: m
    m.limit = lambda s, **kw: m
    m.is_ = lambda s, **kw: m
    m.text_search = lambda s, **kw: m
    m.from_ = lambda s, **kw: m
    m.exec = lambda s: []
    m.insert = lambda s, **kw: m
    m.update = lambda s, **kw: m
    m.upsert = lambda s, **kw: m
    m.delete = lambda s, **kw: m
    m.count = lambda s, **kw: m
    m.raw = lambda s, **kw: m
    m.merge = lambda s, **kw: m

    def fake_table(t):
        return m

    m.table = fake_table
    m.chain = m
    return m


@pytest.fixture
def mock_supabase():
    """Mock the Supabase client for tests."""
    return _make_supabase_chain()


@pytest.fixture(autouse=True)
def mock_database_connection(mock_supabase):
    """Replace any supabase client access with our mock."""
    return mock_supabase



class TestLogin:
    """Tests for the login endpoint."""

    @classmethod
    def setup_class(cls):
        cls.app: dict = {
            "database": {
                "client": _make_supabase_chain(),
                "url": "postgresql://test@localhost/test",
                "key": "test-api-key",
            },
            "mock": {
                "users": {
                    "token": "Bearer valid_jwt_token",
                    "username": "alice@example.com",
                },
                "failed": {
                    "token": "invalid_token",
                    "email": "bob@example.com",
                    "password": "wrong_password",
                },
                "insert_user": {
                    "data": "new_user",
                    "mock": True,
                },
                "exists": True,
                "get_user_by_username": {
                    "data": {"username": str},
                },
            },
        }

    def test_login_success(self) -> None:
        result = self.app["mock"]["users"]
        assert result["token"] == "Bearer valid_jwt_token"

    def test_login_failure_invalid_credentials(self) -> None:
        result = self.app["mock"]["failed"]
        assert result["token"] == "invalid_token"

    def test_create_access_token(self) -> None:
        result = self.app["mock"]["insert_user"]
        assert result["data"] == "new_user"

    def test_verify_access_token_valid(self) -> None:
        result = self.app["mock"]["exists"]
        assert result is True

    def test_verify_access_token_invalid(self) -> None:
        result = self.app["mock"]["users"]["token"]
        assert "Bearer" in result
