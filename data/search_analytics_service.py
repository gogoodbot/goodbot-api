"""
search analytics service
"""

import re
from typing import Any

from data.database_repository import get_database_client
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchAnalyticsService:
    """
    service responsible for persisting search analytics
    """

    def __init__(self):
        self.client = get_database_client()

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        normalize a search query for analytics
        """
        return re.sub(r"\s+", " ", query.strip().lower())

    @staticmethod
    def _get_result_records(search_result: dict[str, Any]) -> list[dict[str, Any]]:
        """
        convert search result groups into generic analytics records

        result positions are scoped to each result type.
        """
        records = []

        for result_type, results in search_result.items():
            if result_type == "query" or not isinstance(results, list):
                continue

            # Current API response uses plural keys.
            # Convert "nonprofits" -> "nonprofit", etc.
            singular_result_type = (
                result_type[:-1] if result_type.endswith("s") else result_type
            )

            for position, result in enumerate(results, start=1):
                result_id = result.get("id")

                if result_id is None:
                    logger.warning(
                        f"Skipping {singular_result_type} search result without an id"
                    )
                    continue

                records.append(
                    {
                        "result_type": singular_result_type,
                        "result_id": result_id,
                        "result_position": position,
                    }
                )

        return records

    def track_search(
        self,
        query: str,
        search_result: dict[str, Any],
        duration_ms: int,
        status: str = "success",
    ) -> None:
        """
        persist analytics for a completed search

        exceptions are intentionally caught here so analytics failures
        never affect the search response.
        """
        try:
            result_records = self._get_result_records(search_result)

            event_response = (
                self.client.table("search_events")
                .insert(
                    {
                        "query": query,
                        "normalized_query": self.normalize_query(query),
                        "result_count": len(result_records),
                        "duration_ms": duration_ms,
                        "status": status,
                    }
                )
                .execute()
            )

            if not event_response.data:
                logger.error("Failed to create search analytics event")
                return

            search_event_id = event_response.data[0]["id"]

            if not result_records:
                return

            event_results = [
                {
                    "search_event_id": search_event_id,
                    **record,
                }
                for record in result_records
            ]

            (self.client.table("search_event_results").insert(event_results).execute())

        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error tracking search analytics: {e}")
