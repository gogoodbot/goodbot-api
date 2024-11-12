"""
user auth/data operations module v1
"""

import bcrypt
from fastapi import APIRouter
from model.user_request_v1 import UserRequest
from .database import user_exists, insert_user, get_user_by_username
# from passlib.context import CryptContext

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

@router.get("/verify")
async def verify_user(username: str, password: str):
    """
    verify if user exists in the database and check if password matches the hashed password
    """
    try:
        # get user from database
        user = get_user_by_username(username=username)
        # check if user exists and password matches with hashed password
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return {"message": "User verified successfully"}
        
        return {"message": "Invalid username or password"}
    except Exception as e:
        print(f"Error verifying user: {e}")
        return {"exception": "Invalid username or password"}

@router.post("/")
async def create_user(user: UserRequest):
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
        else:
            return {"message": "User creation failed"}
    except Exception as e:
        print(f"Error creating user: {e}")
        return {"message": "User creation failed"}
