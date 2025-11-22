"""
User response model (without sensitive fields)
"""
from pydantic import BaseModel


class UserResponse(BaseModel):
    """
    User response model for API responses
    Does not include password or other sensitive fields
    """
    username: str
    active: int
