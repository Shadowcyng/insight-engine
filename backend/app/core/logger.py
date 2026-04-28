import structlog
import logging
import sys
import os
from app.core.config import settings
from utils.constants import LOGGING_DIR
from logging.handlers import RotatingFileHandler
from pathlib import Path

def add_global_info(logger, method_name, event_dict):
    """
    Injects global context into every single log, bypassing contextvars.
    This guarantees these keys survive the middleware clearing the context.
    """
    event_dict["app"] = settings.PROJECT_NAME
    event_dict["env"] = "development" # You can move this to .env later
    event_dict["version"] = "1.0.0"
    return event_dict

def setup_logging():
    """Configures JSON structured logging for the entire app."""
    # 2. Ensure the log directory exists
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    LOGGING_DIR = os.path.join(BASE_DIR, "logs")

# Ensure it exists
    os.makedirs(LOGGING_DIR, exist_ok=True)

    # 3. Setup the standard Python logging root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Clear any existing handlers to prevent duplicate logs
    root_logger.handlers.clear()
    
    # --- HANDLER 1: Console Output (Terminal) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(console_handler)

    # --- HANDLER 2: Rotating File Output (Hard Drive) ---
    # maxBytes=10485760 means it rolls over every 10 MB.
    # backupCount=5 means it keeps insight_engine.log.1, .2, .3, .4, .5

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    file_handler = RotatingFileHandler(
        filename=os.path.join(LOGGING_DIR, "insight_engine.log"),
        maxBytes=10_485_760, 
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            # We output raw JSON. In local dev, you can use ConsoleRenderer for pretty colors,
            # but JSON is mandatory for enterprise production.
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    log = structlog.get_logger()