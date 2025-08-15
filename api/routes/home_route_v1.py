"""
structural subfactors data operations route v1
"""

from fastapi import APIRouter, Depends

from data.database_repository import DatabaseRepository
from usecase.get_homepage_data import GetHomePageData
from model.home_v1 import HomePageData

router = APIRouter(
    prefix="/home",
    tags=["home"],
    responses={404: {"description": "Not found"}}
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
    try:
        # Execute the use case to fetch homepage data
        data = await usecase.execute()
        # If the data is None, return a message
        if data is None:
            return {"message": "No homepage data found"}
        elif not isinstance(data, HomePageData):
            return {"message": "Data is not in the expected format. Current type: " + str(type(data)) + " .. expected type: HomePageData"}

        return data
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching homepage data: {e}")
        return {"message": "Error fetching homepage data"}
