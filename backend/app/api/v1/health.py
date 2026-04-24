from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/")
def health_check():
    return {
        "status" : "online",
        "project_name" : settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }