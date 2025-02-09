"""
user auth operations module v1
"""

from datetime import datetime, timedelta, timezone
import os
from typing import Annotated, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import bcrypt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from api.model.token_v1 import Token
from .database import user_exists, get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "Not found"}}
)


def authenticate_user(username: str, password: str):
    """
    verify if user exists in the database and check if password matches the hashed password
    """
    try:
        # get user from database
        user = get_user_by_username(username=username)
        # check if user exists and password matches with hashed password
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return True

        return False
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error verifying user: {e}")
        return {"exception": "Invalid username or password"}


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    encodes data and creates a jwt encoded access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        os.environ.get("SECRET_KEY"),
        algorithm=os.environ.get("ALGORITHM")
    )
    return encoded_jwt


@router.post("/")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    verify if user exists in the database, check if password matches the stored hashed password,
    authenticate user and return a token
    """
    if not user_exists(value=form_data.username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_authenticated = authenticate_user(
        form_data.username, form_data.password)
    if not user_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        access_token_expires = timedelta(
            milliseconds=int(os.environ.get(
                "ACCESS_TOKEN_EXPIRE_MILLISECONDS"))
        )
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error logging in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


async def verify_access_token(token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
    """
    get current user from database using bearer token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            os.environ.get("SECRET_KEY"),
            algorithms=[os.environ.get("ALGORITHM")]
        )
        token_username: str = payload.get("sub")
        if token_username is None:
            raise credentials_exception
        return payload
    except ExpiredSignatureError as e:
        print(f"JWT expired signature error: {e}")
        raise expired_token_exception from e
    except InvalidTokenError as e:
        print(f"JWT decoding error: {e}")
        raise credentials_exception from e
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error verifying access token: {e}")
        return {"exception": "Unknown error with token"}
