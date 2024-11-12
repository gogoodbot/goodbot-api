"""
user database model
"""
from pydantic import BaseModel

class User(BaseModel):
    """
    user database model
    """
    username: str
    hashed_password: str
    active: int
