"""
auth token model
"""
from pydantic import BaseModel

class Token(BaseModel):
    """
    auth token model
    """
    access_token: str
    token_type: str
