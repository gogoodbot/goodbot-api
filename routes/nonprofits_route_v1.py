"""
experts data operations route v1
"""

from fastapi import APIRouter, Depends

from data.ai_service import AIService
from data.database_repository import DatabaseRepository

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
    page_number: int = 1,
    page_size: int = 10,
    repository: DatabaseRepository = Depends(get_database_repository),
):
    """
    retrieve all nonprofits with pagination
    :param page_number: the page number to fetch
    :param page_size: the number of items per page
    """
    try:
        nonprofits = await repository.get_nonprofits(
            page_number=page_number, page_size=page_size
        )
        return {"data": nonprofits}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching paged nonprofits: {e}")
        return {"message": "Error fetching paged nonprofits"}


@router.get("/summary")
async def generate_entity_summary(service: AIService = Depends(get_ai_service)):
    """
    get user from database by username
    """
    try:
        # token_username: str = access_token.get("sub")
        # ai_summary = await service.generate_entities_hashtag()
        return {"success": "public nonprofits summary api"}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error generating summary: {e}")
        return {"message": "Error generating summary"}


@router.get("/{nonprofit_id}")
async def get_nonprofit_by_id(
    nonprofit_id: str, repository: DatabaseRepository = Depends(get_database_repository)
):
    """
    retrieve nonprofit by id
    """
    try:
        nonprofit = await repository.get_entity_by_nonprofit_id(nonprofit_id)
        if nonprofit is None:
            return {"message": "Nonprofit not found"}
        return {"data": nonprofit}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching nonprofit by id: {e}")
        return {"message": "Error fetching nonprofit by id"}
