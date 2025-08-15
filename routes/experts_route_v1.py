"""
experts data operations route v1
"""

from fastapi import APIRouter, Depends
from data.database_repository import DatabaseRepository

router = APIRouter(
    prefix="/experts",
    tags=["excepts"],
    responses={404: {"description": "Not found"}}
)

def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()

# retrieve all experts with page_size and page_number query parameters
@router.get("/")
async def get_experts(page_number: int = 1, page_size: int = 10, repository: DatabaseRepository = Depends(get_database_repository)):
    """
    retrieve all experts with pagination
    :param page_number: the page number to fetch
    :param page_size: the number of items per page
    """
    try:
        experts = await repository.get_experts(page_number=page_number, page_size=page_size)
        return {"data": experts}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching paged experts: {e}")
        return {"message": "Error fetching paged experts"}


@router.get("/{expert_id}")
async def get_expert_by_id(expert_id: str, repository: DatabaseRepository = Depends(get_database_repository)):
    """
    retrieve expert by id
    """
    try:
        expert = await repository.get_expert_by_id(expert_id)
        if expert is None:
            return {"message": "Expert not found"}
        return {"data": expert}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching expert by id: {e}")
        return {"message": "Error fetching expert by id"}
