"""
main.py

FastAPI Application Server for N100 Financial Intelligence Platform.
Day 38 — Module 6C API Server Scaffold.
"""

import time
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import APP_NAME, VERSION
from src.config.logging_config import get_logger
from src.api.routers import (
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
    health,
)

logger = get_logger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="FastAPI Backend for N100 Financial Intelligence Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# -----------------------------------------------------------------------------
# CORS Middleware Configuration (Allow all origins for internal API service)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Request Logging Middleware
# -----------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log HTTP method, request path, and response execution time for every request.
    """
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - {duration_ms:.2f} ms")
    return response


# -----------------------------------------------------------------------------
# Register Routers under /api/v1 Prefix
# -----------------------------------------------------------------------------
api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router)
api_v1_router.include_router(companies.router)
api_v1_router.include_router(screener.router)
api_v1_router.include_router(sectors.router)
api_v1_router.include_router(peers.router)
api_v1_router.include_router(valuation.router)
api_v1_router.include_router(portfolio.router)
api_v1_router.include_router(documents.router)

app.include_router(api_v1_router)

logger.info("FastAPI Application initialized with 8 routers under /api/v1")
