"""
user data operations module v1
"""

from typing import Annotated, Any, Dict

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from data.database_repository import DatabaseRepository
from model.create_user_request_v1 import CreateUserRequest
from model.user_response_v1 import UserResponse
from utils.logger import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login/")

from .auth_route_v1 import verify_access_token

router = APIRouter(
    prefix="/users", tags=["users"], responses={404: {"description": "Not found"}}
)


def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    access_token: Annotated[Dict[str, Any], Depends(verify_access_token)],
    user: CreateUserRequest,
    repository: DatabaseRepository = Depends(get_database_repository),
):
    """
    hash and salt password, check if user already exists, insert user into database
    """
    # check if user is authenticated
    if not access_token:
        logger.warning("Authentication failed - token missing or invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Username is already lowercased by the validator
    username = user.username

    logger.info(f"Creating user: {username}")

    # check if user already exists
    if repository.user_exists(value=username):
        logger.warning(f"User creation failed - user already exists: {username}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    try:
        # hash password
        hashed_password = bcrypt.hashpw(
            user.password.encode(), bcrypt.gensalt()
        ).decode()

        # insert user into database
        new_user = repository.insert_user(username, hashed_password)

        # check if user was inserted successfully
        if not new_user:
            logger.error(f"Failed to insert user into database: {username}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed",
            )

        logger.info(f"User created successfully: {username}")
        return {"message": "User created successfully", "username": username}
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error creating user {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_user(
    access_token: Annotated[Dict[str, Any], Depends(verify_access_token)],
    repository: DatabaseRepository = Depends(get_database_repository),
) -> UserResponse:
    """
    get current user from database by token username
    """
    token_username: str = access_token.get("sub")
    logger.info(f"Fetching user info for: {token_username}")

    try:
        user = repository.get_user_by_username(token_username)
        if not user:
            logger.error(f"User not found in database: {token_username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserResponse(username=user["username"], active=user["active"])
    except HTTPException:
        raise
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error fetching user {token_username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching user",
        ) from e
