import time
from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.upload import DataUpload
from app.services.analytics_engine import process_file_with_ai

@celery_app.task(bind=True)
def process_data_file(self, record_id: int, file_path: str):
    """
    background task to process the uploaded CSV/JSON file.
    In the real world, this is where Pandas or our AI logic takes over.
    """
    print(f"[Task {self.request.id}] Starting process for DB Record {record_id}...")
    db = SessionLocal()
    try:
        # opening and reading the large file is what we want to simulate as the "heavy lifting" part.
        # We will add real pandas/CSV parsing logic here later.
        record = db.query(DataUpload).filter(DataUpload.id == record_id).first()
        if not record:
            print(f"[Task] Record {record_id} not found in DB.")
            return {"status": "error", "message": "Record not found"}
        
        record.status = "processing"
        db.commit()
        # --- THE REAL WORK ---
        print("[Task] Extracting sample and calling LLM...")
        insight =  process_file_with_ai(file_path)
        record.ai_summary = insight
        # 4. Mark as "Completed"
        record.status = "completed"
        # We could also add a 'rows_processed' column to our DB later and update it here!
        db.commit()
        # return the result of the processing
        print("[Task] AI Analysis finished successfully.")
        return {"record_id": record_id, "status": "completed"}
    
    except Exception as e:
        print(f"[Task] Failed with error: {str(e)}")
        db.rollback()
        record = db.query(DataUpload).filter(DataUpload.id == record_id).first()
        if record:
            record.status = "failed" # IT NOW FAILS CORRECTLY!
            db.commit()
        raise e 
    finally:
        db.close()