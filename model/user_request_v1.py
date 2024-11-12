"""
user auth model
"""
from pydantic import BaseModel

class UserRequest(BaseModel):
    """
    user auth model
    """
    username: str
    password: str
