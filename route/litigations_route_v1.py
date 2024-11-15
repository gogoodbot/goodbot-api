"""
litigations data operations route v1
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from model.user_v1 import User
from .auth_route_v1 import verify_access_token
from .database import get_litigations

router = APIRouter(
    prefix="/litigations",
    tags=["litigations"],
    responses={404: {"description": "Not found"}}
)


@router.get("/")
async def fetch_litigations(access_token: Annotated[User, Depends(verify_access_token)]):
    """
    retrieve all litigations from database
    """
    try:
        litigations = get_litigations()
        return {"data": litigations}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching litigations: {e}")
        return {"message": "Error fetching litigations"}
