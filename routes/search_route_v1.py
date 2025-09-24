"""
text search data operations route v1
"""

from fastapi import APIRouter, Depends

from data.database_repository import DatabaseRepository

router = APIRouter(
    prefix="/search", tags=["search"], responses={404: {"description": "Not found"}}
)


def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


@router.get("/{query}")
async def search(
    query: str, repository: DatabaseRepository = Depends(get_database_repository)
):
    """
    retrieve composite homepage data
    """
    try:
        # Execute the use case to fetch homepage data
        result = await repository.search_by_keywords(query)
        # If the data is None, return a message
        if result is None:
            return {"message": "No homepage data found"}

        return result
    except Exception as e:  # pylint: disable=broad-except
        print(f'Error while searching for "{query}". Exception: {e}')
        return {"message": 'Error while searching for "{query}"'}
