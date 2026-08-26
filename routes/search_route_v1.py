"""
text search data operations route v1
"""

import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from data.database_repository import DatabaseRepository
from data.search_analytics_service import SearchAnalyticsService
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/search", tags=["search"], responses={404: {"description": "Not found"}}
)


def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


def get_search_analytics_service() -> SearchAnalyticsService:
    """
    dependency to get the SearchAnalyticsService instance.
    """
    return SearchAnalyticsService()


@router.get("/{query}")
async def search(
    query: str,
    background_tasks: BackgroundTasks,
    repository: DatabaseRepository = Depends(get_database_repository),
    analytics_service: SearchAnalyticsService = Depends(get_search_analytics_service),
):
    """
    search for entities and experts by keywords
    """
    logger.info(f"Search request for query: {query}")

    # Validate query length
    if len(query) > 500:
        logger.warning(f"Search query too long: {len(query)} characters")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query too long (max 500 characters)",
        )

    if len(query.strip()) < 2:
        logger.warning("Search query too short")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters",
        )

    try:
        start_time = time.perf_counter()

        # Execute the search
        result = await repository.search_by_keywords(query)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # If the data is None, return empty results
        if result is None:
            logger.info(f"No results found for query: {query}")
            return {"nonprofits": [], "experts": [], "query": query}

        # fire off background task to track search event analytics
        background_tasks.add_task(
            analytics_service.track_search,
            query=query,
            search_result=result,
            duration_ms=duration_ms,
        )

        logger.info(f"Search successful for query: {query}")
        return result
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f'Error while searching for "{query}": {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while searching for query",
        ) from e
