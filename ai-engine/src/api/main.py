"""
FastAPI Main Application
Tech News AI Engine API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import health, news


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("=" * 60)
    print("Tech News AI Engine API Starting...")
    print("=" * 60)

    yield

    # Shutdown
    print("Tech News AI Engine API Shutting down...")


app = FastAPI(
    title="Tech News AI Engine",
    description="AI-powered tech news aggregation and processing service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(news.router, prefix="/internal", tags=["News"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Tech News AI Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
