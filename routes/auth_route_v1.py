"""
user auth operations module v1
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from config import get_settings
from data.database_repository import DatabaseRepository
from model.token_v1 import Token
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/login", tags=["login"], responses={404: {"description": "Not found"}}
)


def get_database_repository() -> DatabaseRepository:
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """
    return DatabaseRepository()


def authenticate_user(
    username: str,
    password: str,
    repository: DatabaseRepository = Depends(get_database_repository),
):
    """
    verify if user exists in the database and check if password matches the hashed password
    """
    try:
        # get user from database
        user = repository.get_user_by_username(username=username)
        # check if user exists and password matches with hashed password
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return True

        return False
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error verifying user {username}: {e}")
        return False


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
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


@router.post("/", status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    repository: DatabaseRepository = Depends(get_database_repository),
) -> Token:
    """
    verify if user exists in the database, check if password matches the stored hashed password,
    authenticate user and return a token
    """
    logger.info(f"Login attempt for user: {form_data.username}")

    if not repository.user_exists(value=form_data.username):
        logger.warning(f"Login failed - user not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_authenticated = authenticate_user(form_data.username, form_data.password)
    if not user_authenticated:
        logger.warning(
            f"Login failed - invalid password for user: {form_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        access_token_expires = timedelta(
            milliseconds=settings.access_token_expire_milliseconds
        )
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        logger.info(f"Login successful for user: {form_data.username}")
        return Token(access_token=access_token, token_type="bearer")
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error creating token for user {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create access token",
        ) from e


async def verify_access_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
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
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        token_username: str = payload.get("sub")
        if token_username is None:
            logger.warning("Token validation failed - no username in token")
            raise credentials_exception
        return payload
    except ExpiredSignatureError as e:
        logger.warning(f"JWT expired signature error: {e}")
        raise expired_token_exception from e
    except InvalidTokenError as e:
        logger.warning(f"JWT decoding error: {e}")
        raise credentials_exception from e
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error verifying access token: {e}")
        raise credentials_exception from e
