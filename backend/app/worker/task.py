import time
from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.upload import DataUpload
from app.services.analytics_engine import process_file_with_ai
import structlog


log = structlog.get_logger()

# 1. Define specific exceptions we want to retry.
# We don't retry on ValueError (e.g., bad data) because retrying won't fix bad data.
# We ONLY retry on temporary infrastructure errors.

RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError)

@celery_app.task(
    bind=True,
    autoretry_for=RETRYABLE_EXCEPTIONS,
    retry_kwargs={'max_retries': 5},
    retry_backoff=60,  
    retry_backoff_max=3600, 
    retry_jitter=True
    )
def process_data_file(self, record_id: int, file_path: str):
    """
    background task to process the uploaded CSV/JSON file.
    In the real world, this is where Pandas or our AI logic takes over.
    """
    log.info("process_data_file_task_started", task_id=self.request.id, record_id=record_id, file_path=file_path)
    db = SessionLocal()
    try:
        # opening and reading the large file is what we want to simulate as the "heavy lifting" part.
        # We will add real pandas/CSV parsing logic here later.
        log.debug("fetching_record_from_database", record_id=record_id)
        record = db.query(DataUpload).filter(DataUpload.id == record_id).first()
        if not record:
            log.error("record_not_found_in_database", record_id=record_id, task_id=self.request.id)
            return {"status": "error", "message": "Record not found"}
        
        log.debug("updating_record_status_to_processing", record_id=record_id)
        record.status = "processing"
        db.commit()
        # --- THE REAL WORK ---
        log.info("starting_ai_analysis", record_id=record_id, file_path=file_path)
        insight = process_file_with_ai(file_path)
        log.debug("ai_analysis_completed_successfully", record_id=record_id, insight_length=len(insight))
        
        record.ai_summary = insight
        # 4. Mark as "Completed"
        record.status = "completed"
        # We could also add a 'rows_processed' column to our DB later and update it here!
        db.commit()
        log.info("process_data_file_task_completed_successfully", record_id=record_id, task_id=self.request.id)
        # return the result of the processing
        return {"record_id": record_id, "status": "completed"}
    
    except RETRYABLE_EXCEPTIONS as exc:
        # Celery handles the retry automatically due to 'autoretry_for'.
        # We just log a warning so we can track the instability in Datadog/ELK.
        log.warning(
            "task_failed. retying", 
            record_id=record_id, 
            error=str(exc), 
            attempt=self.request.retries + 1
        )
        raise exc # Must re-raise so Celery knows it failed!
    
    except Exception as e:
        log.error("process_data_file_task_failed", record_id=record_id, task_id=self.request.id, error=str(e))
        db.rollback()
        log.debug("updating_record_status_to_failed", record_id=record_id)
        record = db.query(DataUpload).filter(DataUpload.id == record_id).first()
        if record:
            record.status = "failed" # IT NOW FAILS CORRECTLY!
            db.commit()
        raise e 
    finally:
        db.close()
        log.debug("database_session_closed", record_id=record_id, task_id=self.request.id)