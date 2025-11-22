"""
nonprofits data operations route v1
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from data.ai_service import AIService
from data.database_repository import DatabaseRepository
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/nonprofits",
    tags=["nonprofits"],
    responses={404: {"description": "Not found"}},
)


def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


def get_ai_service() -> AIService:
    """
    dependency to get the AIService instance.
    This allows for easy testing and mocking of the service.
    """
    return AIService()


@router.get("/")
async def get_nonprofits(
    page_number: int = Query(
        default=1, ge=1, le=1000, description="Page number to fetch"
    ),
    page_size: int = Query(
        default=10, ge=1, le=100, description="Number of items per page"
    ),
    repository: DatabaseRepository = Depends(get_database_repository),
):
    """
    retrieve all nonprofits with pagination
    :param page_number: the page number to fetch (1-1000)
    :param page_size: the number of items per page (1-100)
    """
    logger.info(f"Fetching nonprofits - page: {page_number}, size: {page_size}")

    try:
        nonprofits = await repository.get_nonprofits(
            page_number=page_number, page_size=page_size
        )
        if nonprofits is None:
            logger.warning("No nonprofits found or database error")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No nonprofits found"
            )
        logger.info(f"Successfully fetched {len(nonprofits)} nonprofits")
        return {"data": nonprofits, "page": page_number, "page_size": page_size}
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching nonprofits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching nonprofits",
        ) from e


@router.get("/summary")
async def generate_entity_summary(service: AIService = Depends(get_ai_service)):
    """
    Generate entity summaries using AI service
    Note: This endpoint is currently a placeholder
    """
    logger.info("Summary generation endpoint called (placeholder)")
    # TODO: Implement actual summary generation
    # ai_summary = await service.generate_entities_hashtag()
    return {"success": "public nonprofits summary api", "status": "not_implemented"}


@router.get("/{nonprofit_id}")
async def get_nonprofit_by_id(
    nonprofit_id: str, repository: DatabaseRepository = Depends(get_database_repository)
):
    """
    retrieve nonprofit entity by nonprofit id
    """
    logger.info(f"Fetching nonprofit by id: {nonprofit_id}")

    try:
        nonprofit = await repository.get_entity_by_nonprofit_id(nonprofit_id)
        if nonprofit is None or len(nonprofit) == 0:
            logger.warning(f"Nonprofit not found: {nonprofit_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nonprofit not found with id: {nonprofit_id}",
            )
        logger.info(f"Successfully fetched nonprofit: {nonprofit_id}")
        return {"data": nonprofit}
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching nonprofit {nonprofit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching nonprofit",
        ) from e
