"""
main module
"""

from fastapi import FastAPI

from .routes import auth_route_v1, litigations_route_v1, users_route_v1, home_route_v1
from .routes.middleware import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

def create_app():
    """
    create FastAPI app
    """
    fastapi = FastAPI()
    fastapi.include_router(auth_route_v1.router, prefix="/v1")
    fastapi.include_router(users_route_v1.router, prefix="/v1")
    fastapi.include_router(litigations_route_v1.router, prefix="/v1")
    fastapi.include_router(home_route_v1.router, prefix="/v1")
    return fastapi


app = create_app()

# add custom authentication to app
app.add_middleware(AuthMiddleware)
app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)
