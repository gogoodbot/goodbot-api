from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from data.database_repository import DatabaseRepository, get_database_client


class TestGetDatabaseClient:
    def test_creates_database_client(self):
        get_database_client.cache_clear()

        with patch("data.database_repository.create_client") as mock_create:
            mock_create.return_value = MagicMock()

            result = get_database_client()

            mock_create.assert_called_once()
            assert result == mock_create.return_value

    def test_returns_cached_client(self):
        get_database_client.cache_clear()

        with patch("data.database_repository.create_client") as mock_create:
            mock_create.return_value = MagicMock()

            first = get_database_client()
            second = get_database_client()

            assert first is second
            mock_create.assert_called_once()


class TestDatabaseRepository:
    @pytest.fixture
    def repository(self):
        with patch("data.database_repository.get_database_client") as mock_client:
            mock_client.return_value = MagicMock()
            repo = DatabaseRepository()
            yield repo

    def test_user_exists_active_user(self, repository):
        response = MagicMock()
        response.data = [{"active": 1}]
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        result = repository.user_exists("TestUser")

        assert result is True

    def test_user_exists_inactive_user(self, repository):
        response = MagicMock()
        response.data = [{"active": 0}]
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        assert repository.user_exists("TestUser") is False

    def test_user_exists_user_not_found(self, repository):
        response = MagicMock()
        response.data = []
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        assert repository.user_exists("TestUser") is False

    def test_user_exists_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert repository.user_exists("TestUser") is False

    def test_get_user_by_username(self, repository):
        response = MagicMock()
        response.data = [{"username": "testuser"}]
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        result = repository.get_user_by_username("TestUser")

        assert result == {"username": "testuser"}

    def test_get_user_by_username_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert repository.get_user_by_username("TestUser") is None

    def test_insert_user(self, repository):
        response = MagicMock()
        response.data = [{"username": "testuser"}]
        repository.client.table.return_value.insert.return_value.execute.return_value = (
            response
        )

        result = repository.insert_user("TestUser", "hashed-password")

        assert result == response.data
        repository.client.table.return_value.insert.assert_called_once_with(
            {
                "username": "testuser",
                "password": "hashed-password",
            }
        )

    def test_insert_user_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert repository.insert_user("TestUser", "hash") is None

    def test_get_litigations(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.table.return_value.select.return_value.execute.return_value = (
            response
        )

        assert repository.get_litigations() == response.data

    def test_get_litigations_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert repository.get_litigations() is None

    @pytest.mark.asyncio
    async def test_get_homepage_data(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.rpc.return_value.execute.return_value = response

        result = await repository.get_homepage_data()

        assert result == response.data
        repository.client.rpc.assert_called_once_with("get_homepage_data2")

    @pytest.mark.asyncio
    async def test_get_homepage_data_exception(self, repository):
        repository.client.rpc.side_effect = Exception("DB error")

        assert await repository.get_homepage_data() is None

    @pytest.mark.asyncio
    async def test_get_structural_subfactors(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.table.return_value.select.return_value.execute.return_value = (
            response
        )

        assert await repository.get_structural_subfactors() == response.data

    @pytest.mark.asyncio
    async def test_get_structural_subfactors_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_structural_subfactors() is None

    @pytest.mark.asyncio
    async def test_get_experts_paginated(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.table.return_value.select.return_value.range.return_value.execute.return_value = (
            response
        )

        result = await repository.get_experts(page_number=2, page_size=10)

        assert result == response.data
        repository.client.table.return_value.select.return_value.range.assert_called_once_with(
            10, 19
        )

    @pytest.mark.asyncio
    async def test_get_experts_all(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.table.return_value.select.return_value.execute.return_value = (
            response
        )

        result = await repository.get_experts(page_size=-1)

        assert result == response.data

    @pytest.mark.asyncio
    async def test_get_experts_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_experts() is None

    @pytest.mark.asyncio
    async def test_get_expert_by_id(self, repository):
        response = MagicMock()
        response.data = [{"id": "123"}]
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        assert await repository.get_expert_by_id("123") == response.data

    @pytest.mark.asyncio
    async def test_get_expert_by_id_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_expert_by_id("123") is None

    @pytest.mark.asyncio
    async def test_update_expert_by_id(self, repository):
        response = MagicMock()
        response.data = [{"id": "123", "name": "Updated"}]
        repository.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            response
        )

        result = await repository.update_expert_by_id("123", {"name": "Updated"})

        assert result == response.data

    @pytest.mark.asyncio
    async def test_update_expert_by_id_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.update_expert_by_id("123", {}) is None

    @pytest.mark.asyncio
    async def test_get_nonprofits(self, repository):
        response = MagicMock()
        response.data = [{"id": "np1"}, {"id": "np2"}]
        repository.client.table.return_value.select.return_value.range.return_value.execute.return_value = (
            response
        )

        repository.get_entity_by_nonprofit_id = AsyncMock(
            side_effect=[
                [{"id": "entity1"}],
                [{"id": "entity2"}],
            ]
        )

        result = await repository.get_nonprofits(1, 2)

        assert result == [{"id": "entity1"}, {"id": "entity2"}]

    @pytest.mark.asyncio
    async def test_get_nonprofits_no_data(self, repository):
        response = MagicMock()
        response.data = []
        repository.client.table.return_value.select.return_value.range.return_value.execute.return_value = (
            response
        )

        assert await repository.get_nonprofits() is None

    @pytest.mark.asyncio
    async def test_get_nonprofits_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_nonprofits() is None

    @pytest.mark.asyncio
    async def test_get_entity_by_nonprofit_id(self, repository):
        response = MagicMock()
        response.data = [{"id": "np1"}]
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        assert await repository.get_entity_by_nonprofit_id("np1") == response.data

    @pytest.mark.asyncio
    async def test_get_entity_by_nonprofit_id_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_entity_by_nonprofit_id("np1") is None

    @pytest.mark.asyncio
    async def test_get_entity_by_id(self, repository):
        response = MagicMock()
        response.data = [{"id": "entity1"}]
        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            response
        )

        assert await repository.get_entity_by_id("entity1") == response.data

    @pytest.mark.asyncio
    async def test_get_entity_by_id_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_entity_by_id("entity1") is None

    @pytest.mark.asyncio
    async def test_get_entities_paginated(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.table.return_value.select.return_value.range.return_value.execute.return_value = (
            response
        )

        result = await repository.get_entities(2, 4)

        assert result == response.data
        repository.client.table.return_value.select.return_value.range.assert_called_once_with(
            4, 7
        )

    @pytest.mark.asyncio
    async def test_get_entities_all(self, repository):
        response = MagicMock()
        response.data = [{"id": 1}]
        repository.client.table.return_value.select.return_value.execute.return_value = (
            response
        )

        assert await repository.get_entities(page_size=-1) == response.data

    @pytest.mark.asyncio
    async def test_get_entities_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.get_entities() is None

    @pytest.mark.asyncio
    async def test_update_entity_by_id(self, repository):
        response = MagicMock()
        response.data = [{"id": "entity1", "name": "Updated"}]
        repository.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            response
        )

        result = await repository.update_entity_by_id("entity1", {"name": "Updated"})

        assert result == response.data

    @pytest.mark.asyncio
    async def test_update_entity_by_id_exception(self, repository):
        repository.client.table.side_effect = Exception("DB error")

        assert await repository.update_entity_by_id("entity1", {}) is None

    @pytest.mark.asyncio
    async def test_search_by_keywords(self, repository):
        entity_response = MagicMock()
        entity_response.data = [{"id": "entity1"}]

        expert_response = MagicMock()
        expert_response.data = [{"id": "expert1"}]

        entity_search_response = MagicMock()
        entity_search_response.data = [{"id": "entity1"}]

        repository.client.from_.return_value.select.return_value.text_search.return_value.execute.return_value = (
            entity_response
        )
        repository.client.rpc.return_value.execute.side_effect = [
            expert_response,
            entity_search_response,
        ]

        nonprofit_response = MagicMock()
        nonprofit_response.data = [{"id": "np1", "entity_id": "entity1"}]

        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            nonprofit_response
        )

        result = await repository.search_by_keywords("education health")

        assert result == {
            "nonprofits": [{"id": "entity1"}],
            "experts": [{"id": "expert1"}],
        }

    @pytest.mark.asyncio
    async def test_search_by_keywords_removes_special_characters(self, repository):
        entity_response = MagicMock()
        entity_response.data = []

        expert_response = MagicMock()
        expert_response.data = []

        entity_search_response = MagicMock()
        entity_search_response.data = []

        repository.client.from_.return_value.select.return_value.text_search.return_value.execute.return_value = (
            entity_response
        )
        repository.client.rpc.return_value.execute.side_effect = [
            expert_response,
            entity_search_response,
        ]

        result = await repository.search_by_keywords("hello! @world#")

        assert result == {
            "nonprofits": [],
            "experts": [],
        }

    @pytest.mark.asyncio
    async def test_search_by_keywords_empty_after_sanitization(self, repository):
        result = await repository.search_by_keywords("!@#$%^&*()")

        assert result == {
            "nonprofits": [],
            "experts": [],
        }

    @pytest.mark.asyncio
    async def test_search_by_keywords_exception(self, repository):
        repository.client.from_.side_effect = Exception("DB error")

        assert await repository.search_by_keywords("test") is None
