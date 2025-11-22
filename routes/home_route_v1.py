"""
home page data operations route v1
"""

from fastapi import APIRouter, Depends, HTTPException, status

from data.database_repository import DatabaseRepository
from model.home_v1 import HomePageData
from usecase.get_homepage_data import GetHomePageData
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/home", tags=["home"], responses={404: {"description": "Not found"}}
)


def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


def get_homepage_data() -> GetHomePageData:
    """
    dependency to get the GetHomePageData use case instance.
    This allows for easy testing and mocking of the use case.
    """
    return GetHomePageData(repository=get_database_repository())


@router.get("/")
async def get_home_page(usecase: GetHomePageData = Depends(get_homepage_data)):
    """
    retrieve composite homepage data
    """
    logger.info("Fetching homepage data")

    try:
        # Execute the use case to fetch homepage data
        data = await usecase.execute()

        # If the data is None, return error
        if data is None:
            logger.warning("No homepage data found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No homepage data found"
            )

        # Validate data type
        if not isinstance(data, HomePageData):
            logger.error(f"Invalid data type returned: {type(data)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid data format from database",
            )

        logger.info("Successfully fetched homepage data")
        return data
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching homepage data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching homepage data",
        ) from e
