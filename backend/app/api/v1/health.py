from fastapi import APIRouter
from app.core.config import settings
import structlog

log = structlog.get_logger()
router = APIRouter()

@router.get("/")
def health_check():
    log.info("health_check_request")
    try:
        result = {
            "status" : "online",
            "project_name" : settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT
        }
        log.debug("health_check_passed", status=result["status"])
        return result
    except Exception as e:
        log.error("health_check_failed", error=str(e))
        return {"status": "error", "error": str(e)}