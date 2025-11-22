"""
user auth model
"""
import re
from pydantic import BaseModel, Field, field_validator


class CreateUserRequest(BaseModel):
    """
    create user auth model with validation
    """
    username: str = Field(..., min_length=3, max_length=255, description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")

    @field_validator('username')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength
        Requirements: min 8 chars, uppercase, lowercase, number
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
