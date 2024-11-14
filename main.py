"""
main module
"""
from fastapi import FastAPI
from route import auth_route_v1, litigations_route_v1, user_route_v1

def create_app():
    """
    create FastAPI app
    """
    fastapi = FastAPI()
    fastapi.include_router(auth_route_v1.router)
    fastapi.include_router(auth_route_v1.router, prefix="/v1")
    fastapi.include_router(user_route_v1.router)
    fastapi.include_router(user_route_v1.router, prefix="/v1")
    fastapi.include_router(litigations_route_v1.router)
    fastapi.include_router(litigations_route_v1.router, prefix="/v1")
    return fastapi

app = create_app()
