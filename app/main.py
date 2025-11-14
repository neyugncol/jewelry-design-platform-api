"""Main FastAPI application."""
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import init_db
from app.api import users, chat, conversations, images


logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: Cleanup if needed
    pass


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI-powered jewelry design assistant API for PNJ Jewelry Corp.

    This API allows users to:
    - Chat with an AI assistant to design custom jewelry
    - Generate 2D jewelry design images from descriptions
    - Create 3D models from 2D designs (placeholder)
    - Manage design conversations and history

    Powered by Google Gemini Flash 2.0 and Gemini 2.5 Flash Image.
    """,
    lifespan=lifespan,
    debug=True
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(images.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PNJ Jewelry AI Designer API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["disable_existing_loggers"] = False
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level='info' if not settings.debug else 'debug',
        log_config=log_config
    )
