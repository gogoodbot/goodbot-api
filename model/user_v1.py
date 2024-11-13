"""
user database model
"""
from pydantic import BaseModel

class User(BaseModel):
    """
    user database model
    """
    username: str
    password: str
    active: int
