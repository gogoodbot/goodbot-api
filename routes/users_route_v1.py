"""
user data operations module v1
"""

from typing import Annotated, Dict, Any
import bcrypt
from fastapi import APIRouter, Depends
from model.create_user_request_v1 import CreateUserRequest
from model.user_v1 import User
from .auth_route_v1 import verify_access_token
from data.database_repository import DatabaseRepository

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


@router.post("/")
async def create_user(user: CreateUserRequest, repository: DatabaseRepository = Depends(get_database_repository)):
    """
    hash and salt password, check if user already exists, insert user into database
    """
    try:
        # convert email to lowercase
        username = user.username.lower()

        # hash password
        hashed_password = bcrypt.hashpw(
            user.password.encode(), bcrypt.gensalt()).decode()

        # check if user already exists
        if repository.user_exists(value=username):
            return {"message": "User already exists"}

        # insert user into database
        new_user = repository.insert_user(username, hashed_password)

        # check if user was inserted successfully
        if new_user:
            return {"message": "User created successfully"}

        return {"message": "User creation failed"}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error creating user: {e}")
        return {"message": "User creation failed"}


@router.get("/me", response_model=User)
async def get_user(access_token: Annotated[Dict[str, Any], Depends(verify_access_token)], repository: DatabaseRepository = Depends(get_database_repository)):
    """
    get user from database by username
    """
    try:
        token_username: str = access_token.get("sub")
        user = repository.get_user_by_username(token_username)
        if not user:
            return {"message": "Invalid access token. No username found in token."}
        return user
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching user: {e}")
        return {"message": "Error fetching user"}


@router.get("/test")
async def test():
    """
    get user from database by username
    """
    try:
        # token_username: str = access_token.get("sub")
        return {"success": "public api"}
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching user: {e}")
        return {"message": "Error fetching user"}
