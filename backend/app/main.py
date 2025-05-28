from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any
import uvicorn

from app.core.config import settings
from app.db.database import init_database, close_database
from app.core.rate_limiter import rate_limiter
from app.api.auth.user_context import user_manager

from app.api.auth.auth_routes import router as auth_router
from app.api.research.research_routes import router as research_router
from app.api.collab_routes import router as collaboration_router


logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Current user: {settings.CURRENT_USER}")
    logger.info(f"Timestamp: {settings.CURRENT_TIMESTAMP}")
    
    try:
        await init_database()
        await rate_limiter.init_redis()
        logger.info("Application startup completed successfully")
        yield
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

    logger.info("Shutting down application...")
    try:
        await close_database()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Application shutdown error: {str(e)}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Multi-Agent Research Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["perplexiquest.com", "app.perplexiquest.com"]
)

@app.middleware("http")
async def process_request(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    if settings.RATE_LIMIT_ENABLED:
        rate_limit_passed = await rate_limiter.check_rate_limit(
            f"global:{client_ip}", 
            max_attempts=1000, 
            window_minutes=60
        )
        if not rate_limit_passed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests from this IP address",
                    "timestamp": settings.CURRENT_TIMESTAMP
                }
            )
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Timestamp"] = settings.CURRENT_TIMESTAMP
        response.headers["X-User-Context"] = settings.CURRENT_USER
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"IP: {client_ip}"
        )
        
        return response
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": settings.CURRENT_TIMESTAMP
            }
        )

app.include_router(auth_router)
app.include_router(research_router)
app.include_router(collaboration_router)

@app.get("/health")
async def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": settings.CURRENT_TIMESTAMP,
        "user": settings.CURRENT_USER
    }

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else None,
        "timestamp": settings.CURRENT_TIMESTAMP,
        "status": "operational"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": settings.CURRENT_TIMESTAMP,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": settings.CURRENT_TIMESTAMP,
            "path": str(request.url.path)
        }
    )

if settings.DEBUG:
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        pass

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True
    )