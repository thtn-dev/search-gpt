import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.v1.router import api_router_v1
from app.config.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    logger.info("Starting...")
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Search API",
        description="API for searching URLs",
        version="1.0.0",
    )
    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Health check endpoint
    @application.get("/health", tags=["health"])
    async def health() -> dict:
        """Health check endpoint"""
        return {"status": "healthy"}

    # Root endpoint
    @application.get("/", tags=["root"])
    async def root() -> dict:
        """Root endpoint"""
        return {"message": "Welcome to the Gemini Chat API!"}    
     # Include API router
    application.include_router(api_router_v1, prefix="/v1")
    return application

app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
    