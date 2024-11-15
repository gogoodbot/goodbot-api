"""
middleware API interceptor
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from route.auth_route_v1 import verify_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    """
    authentication middleware
    """

    async def dispatch(self, request: Request, call_next):
        """
        checks if user is authenticated
        """
        if not request.headers.get("Authorization"):
            return await call_next(request)

        # get access token from request headers
        access_token = request.headers.get("Authorization").split(" ")[1]

        # check if access token is validn
        try:
            print(f"Access token: {access_token}")
            access_token = await verify_access_token(access_token)
            if access_token:
                return await call_next(request)
        except HTTPException as e:
            # If token validation fails due to HTTPException, return the error response
            return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)
        except Exception as e:  # pylint: disable=broad-except
            # If token validation fails due to other exceptions, return a generic error response
            return JSONResponse(content={"detail": f"Error: {str(e)}"}, status_code=500)
