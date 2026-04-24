from fastapi import APIRouter
from app.api.v1 import health
from app.api.v1 import uploads
from app.api.v1 import auth

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(uploads.router, prefix="/upload", tags=["Data Processing"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])