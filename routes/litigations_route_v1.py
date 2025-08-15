"""
litigations data operations route v1
"""

from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends
from .auth_route_v1 import verify_access_token
from data.database_repository import DatabaseRepository

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
async def fetch_litigations(_: Annotated[Dict[str, Any], Depends(verify_access_token)], repository: DatabaseRepository = Depends(get_database_repository)):
    """
    retrieve all litigations from database
    """
    try:
        litigations = repository.get_litigations()
        return {"data": litigations}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching litigations: {e}")
        return {"message": "Error fetching litigations"}
