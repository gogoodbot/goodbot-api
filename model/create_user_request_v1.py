"""
user auth model
"""
from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    """
    create user auth model
    """
    username: str
    password: str
