"""
experts data operations route v1
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from data.database_repository import DatabaseRepository
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/experts",
    tags=["experts"],  # Fixed typo: was "excepts"
    responses={404: {"description": "Not found"}}
)

def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()

@router.get("/")
async def get_experts(
    page_number: int = Query(default=1, ge=1, le=1000, description="Page number to fetch"),
    page_size: int = Query(default=10, ge=-1, le=100, description="Number of items per page, -1 for all"),
    repository: DatabaseRepository = Depends(get_database_repository)
):
    """
    retrieve all experts with pagination
    :param page_number: the page number to fetch (1-1000)
    :param page_size: the number of items per page (1-100, or -1 for all)
    """
    logger.info(f"Fetching experts - page: {page_number}, size: {page_size}")

    try:
        experts = await repository.get_experts(page_number=page_number, page_size=page_size)
        if experts is None:
            logger.warning("No experts found or database error")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No experts found"
            )
        logger.info(f"Successfully fetched {len(experts)} experts")
        return {"data": experts, "page": page_number, "page_size": page_size}
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching experts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching experts"
        ) from e


@router.get("/{expert_id}")
async def get_expert_by_id(expert_id: str, repository: DatabaseRepository = Depends(get_database_repository)):
    """
    retrieve expert by id
    """
    logger.info(f"Fetching expert by id: {expert_id}")

    try:
        expert = await repository.get_expert_by_id(expert_id)
        if expert is None or len(expert) == 0:
            logger.warning(f"Expert not found: {expert_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expert not found with id: {expert_id}"
            )
        logger.info(f"Successfully fetched expert: {expert_id}")
        return {"data": expert}
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching expert {expert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching expert"
        ) from e
