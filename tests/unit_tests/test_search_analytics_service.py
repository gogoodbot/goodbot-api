"""
unit tests for search analytics service
"""

from unittest.mock import MagicMock, patch

from data.search_analytics_service import SearchAnalyticsService


class TestSearchAnalyticsService:
    """Tests for SearchAnalyticsService."""

    def setup_method(self):
        """Set up the service with a mocked database client."""
        self.client_patcher = patch("data.search_analytics_service.get_database_client")
        self.mock_get_database_client = self.client_patcher.start()

        self.mock_client = MagicMock()
        self.mock_get_database_client.return_value = self.mock_client

        self.service = SearchAnalyticsService()

    def teardown_method(self):
        """Stop patches."""
        self.client_patcher.stop()

    def test_normalize_query(self):
        """Should trim, lowercase, and collapse whitespace."""
        result = self.service.normalize_query("   PeaceGeeks    Vancouver   ")

        assert result == "peacegeeks vancouver"

    def test_get_result_records_with_multiple_result_types(self):
        """Should create records for each result and preserve positions per type."""
        search_result = {
            "nonprofits": [
                {"id": "nonprofit-1"},
                {"id": "nonprofit-2"},
            ],
            "experts": [
                {"id": "expert-1"},
                {"id": "expert-2"},
            ],
        }

        records = self.service._get_result_records(search_result)

        assert records == [
            {
                "result_type": "nonprofit",
                "result_id": "nonprofit-1",
                "result_position": 1,
            },
            {
                "result_type": "nonprofit",
                "result_id": "nonprofit-2",
                "result_position": 2,
            },
            {
                "result_type": "expert",
                "result_id": "expert-1",
                "result_position": 1,
            },
            {
                "result_type": "expert",
                "result_id": "expert-2",
                "result_position": 2,
            },
        ]

    def test_get_result_records_with_zero_results(self):
        """Should return an empty list when no results are returned."""
        search_result = {
            "nonprofits": [],
            "experts": [],
        }

        records = self.service._get_result_records(search_result)

        assert records == []

    def test_track_search_creates_event_and_results(self):
        """Should create a search event and associated result records."""
        event_response = MagicMock()
        event_response.data = [{"id": "search-event-1"}]

        events_table = MagicMock()
        events_table.insert.return_value.execute.return_value = event_response

        results_table = MagicMock()

        def table_side_effect(table_name):
            if table_name == "search_events":
                return events_table
            if table_name == "search_event_results":
                return results_table
            raise ValueError(f"Unexpected table: {table_name}")

        self.mock_client.table.side_effect = table_side_effect

        search_result = {
            "nonprofits": [
                {"id": "nonprofit-1"},
            ],
            "experts": [
                {"id": "expert-1"},
            ],
        }

        self.service.track_search(
            query="  PeaceGeeks  ",
            search_result=search_result,
            duration_ms=123,
        )

        events_table.insert.assert_called_once_with(
            {
                "query": "  PeaceGeeks  ",
                "normalized_query": "peacegeeks",
                "result_count": 2,
                "duration_ms": 123,
                "status": "success",
            }
        )

        results_table.insert.assert_called_once_with(
            [
                {
                    "search_event_id": "search-event-1",
                    "result_type": "nonprofit",
                    "result_id": "nonprofit-1",
                    "result_position": 1,
                },
                {
                    "search_event_id": "search-event-1",
                    "result_type": "expert",
                    "result_id": "expert-1",
                    "result_position": 1,
                },
            ]
        )

    def test_track_search_with_zero_results_creates_only_event(self):
        """Should create a search event but no result records."""
        event_response = MagicMock()
        event_response.data = [{"id": "search-event-1"}]

        events_table = MagicMock()
        events_table.insert.return_value.execute.return_value = event_response

        self.mock_client.table.return_value = events_table

        self.service.track_search(
            query="something missing",
            search_result={
                "nonprofits": [],
                "experts": [],
            },
            duration_ms=50,
        )

        events_table.insert.assert_called_once_with(
            {
                "query": "something missing",
                "normalized_query": "something missing",
                "result_count": 0,
                "duration_ms": 50,
                "status": "success",
            }
        )

        self.mock_client.table.assert_called_once_with("search_events")

    def test_track_search_does_not_raise_when_database_fails(self):
        """Analytics failures should be isolated and not raise exceptions."""
        self.mock_client.table.side_effect = Exception("Supabase connection failed")

        search_result = {
            "nonprofits": [
                {"id": "nonprofit-1"},
            ],
            "experts": [],
        }

        self.service.track_search(
            query="test_nonprofit",
            search_result=search_result,
            duration_ms=100,
        )
