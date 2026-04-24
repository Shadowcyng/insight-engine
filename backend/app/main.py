from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, 
              description="Data processing and AI insight platform",
              version="1.0.0",
              openapi_url="/api/v1/openapi.json",
              docs_url="/api/v1/docs"
              )

app.include_router(api_router, prefix="/api/v1")