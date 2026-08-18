"""
main module
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes import (auth_route_v1, experts_route_v1, home_route_v1,
                    litigations_route_v1, nonprofits_route_v1, search_route_v1,
                    users_route_v1)
from utils.logger import get_logger, setup_logging

# Setup logging on application startup
setup_logging()
logger = get_logger(__name__)

# Load settings
settings = get_settings()


def create_app():
    """
    create FastAPI app
    """
    fastapi = FastAPI(
        title="GoodBot API",
        description="Backend API for the GoodBot Project",
        version="1.0.0",
    )
    fastapi.include_router(auth_route_v1.router, prefix="/v1")
    fastapi.include_router(users_route_v1.router, prefix="/v1")
    fastapi.include_router(litigations_route_v1.router, prefix="/v1")
    fastapi.include_router(home_route_v1.router, prefix="/v1")
    fastapi.include_router(experts_route_v1.router, prefix="/v1")
    fastapi.include_router(nonprofits_route_v1.router, prefix="/v1")
    fastapi.include_router(search_route_v1.router, prefix="/v1")

    logger.info("FastAPI application created successfully")
    return fastapi


app = create_app()

# add CORS middleware to app
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https:\/\/.*-goodbot\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured with origins: {settings.cors_origins_list}")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "goodbot-api"}
