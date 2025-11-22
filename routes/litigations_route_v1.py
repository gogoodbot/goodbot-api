"""
litigations data operations route v1
"""

from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from data.database_repository import DatabaseRepository
from utils.logger import get_logger

from .auth_route_v1 import verify_access_token

logger = get_logger(__name__)

router = APIRouter(
    prefix="/litigations",
    tags=["litigations"],
    responses={404: {"description": "Not found"}}
)

def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


@router.get("/")
async def fetch_litigations(
    _: Annotated[Dict[str, Any], Depends(verify_access_token)],
    repository: DatabaseRepository = Depends(get_database_repository)
):
    """
    retrieve all litigations from database (requires authentication)
    """
    logger.info("Fetching all litigations")

    try:
        litigations = repository.get_litigations()
        if litigations is None:
            logger.warning("No litigations found or database error")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No litigations found"
            )
        logger.info(f"Successfully fetched {len(litigations)} litigations")
        return {"data": litigations}
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching litigations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching litigations"
        ) from e
