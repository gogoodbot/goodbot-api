"""
user data operations module v1
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from model.user_v1 import User
from .auth_route_v1 import get_current_active_user
from .database import get_litigations

router = APIRouter(
    prefix="/litigations",
    tags=["litigations"],
    responses={404: {"description": "Not found"}}
)

@router.post("/")
async def fetch_litigations(current_user: Annotated[User, Depends(get_current_active_user)]):
    """
    retrieve all litigations from database
    """
    try:
        if not current_user:
            return {"message": "Invalid access token. In order to access protected routes, you \
                    must be logged in."}
        litigations = get_litigations()
        return {"data": litigations}
    except Exception as e: # pylint: disable=broad-except
        print(f"Error fetching litigations: {e}")
        return {"message": "Error fetching litigations"}
