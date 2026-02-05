"""
StochastiQdata API - Main Application
FastAPI backend for dataset rating platform for actuaries
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.middleware.supabase_auth import SupabaseAuthMiddleware
from app.api import datasets, reviews, notebooks, benchmarks, favorites

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API de notation de datasets pour actuaires",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase authentication middleware
app.add_middleware(SupabaseAuthMiddleware)

# Include routers
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(notebooks.router, prefix="/api/v1")
app.include_router(benchmarks.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
