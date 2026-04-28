from fastapi import FastAPI, Request, WebSocket
from app.api.v1.api import api_router
from app.core.config import settings
import uuid
import structlog
from app.core.logger import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.websocket import router as wsRouter

setup_logging()

origins = [
    "*",
]


log=structlog.get_logger()
app = FastAPI(title=settings.PROJECT_NAME, 
              description="Data processing and AI insight platform",
              version="1.0.0",
              openapi_url="/api/v1/openapi.json",
              docs_url="/api/v1/docs"
              )


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Minor comment: This is strictly required for HttpOnly cookies
    allow_methods=["*"],    # Minor comment: Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)



@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Generate a unique ID for this specific API call
    scope_type = request.scope.get("type")
    log.info("request_scope", type=scope_type)    
    if scope_type == "websocket" or request.headers.get("upgrade") == "websocket":
        return await call_next(request)
    request_id = str(uuid.uuid4())

    # Bind this ID to the structlog context globally for this request
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )
    log.info("request_started")
    try:
        response = await call_next(request)
        # Log successful completion with the status code
        log.info("request_finished", status_code=response.status_code)
        return response
    except Exception as e:
        # Log crashes with full stack traces
        log.error("request_failed", error=str(e))
        raise e
    
app.include_router(wsRouter, prefix="/api/v1/ws", tags=["Websocket"])

app.include_router(api_router, prefix="/api/v1")


