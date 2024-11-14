"""
user data operations module v1
"""

from typing import Annotated
import bcrypt
from fastapi import APIRouter, Depends
from model.create_user_request_v1 import CreateUserRequest
from model.user_v1 import User
from .auth_route_v1 import get_current_active_user
from .database import user_exists, insert_user

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

@router.post("/")
async def create_user(user: CreateUserRequest):
    """
    hash and salt password, check if user already exists, insert user into database
    """
    try:
        # convert email to lowercase
        username = user.username.lower()

        # hash password
        hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

        # check if user already exists
        if user_exists(value=username):
            return {"message": "User already exists"}

        # insert user into database
        new_user = insert_user(username, hashed_password)

        # check if user was inserted successfully
        if new_user:
            return {"message": "User created successfully"}

        return {"message": "User creation failed"}
    except Exception as e: # pylint: disable=broad-except
        print(f"Error creating user: {e}")
        return {"message": "User creation failed"}

@router.get("/me", response_model=User)
async def get_user(current_user: Annotated[User, Depends(get_current_active_user)]):
    """
    get user from database by username
    """
    return current_user
