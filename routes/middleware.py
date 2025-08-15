"""
middleware API interceptor
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from routes.auth_route_v1 import verify_access_token


class AuthMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """
    authentication middleware
    """

    async def dispatch(self, request: Request, call_next):
        """
        checks if user is authenticated
        """
        if not request.headers.get("Authorization"):
            return await call_next(request)

        # check if access token is valid
        try:
            # get access token from request headers
            access_token = request.headers.get("Authorization").split(" ")[1]
            token = await verify_access_token(access_token)
            if token:
                return await call_next(request)
        except HTTPException as e:
            print(f"AuthMiddleware HTTPException: {e}")
            # If token validation fails due to HTTPException, return the error response
            return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)
        except Exception as e:  # pylint: disable=broad-except
            print(f"AuthMiddleware Exception: {e}")
            # If token validation fails due to other exceptions, return a generic error response
            return JSONResponse(content={"detail": f"Error: {str(e)}"}, status_code=500)
