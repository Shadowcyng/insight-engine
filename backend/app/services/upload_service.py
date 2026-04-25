from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.upload import DataUpload
from utils.constants import STORAGE_DIR
import os
import shutil
import structlog

log = structlog.get_logger()

# Our local "S3 Bucket" equivalent
os.makedirs(STORAGE_DIR, exist_ok=True)


def process_and_upload_file(db: Session,upload_file: UploadFile, owner_id: int)-> DataUpload:
    log.info("processing_upload_file", filename=upload_file.filename, owner_id=owner_id)
    try:
        # Step 1: Prepare the record
        record = DataUpload(filename=upload_file.filename, status="pending", owner_id=owner_id)
        # Step 2: Save the file to disk
        db.add(record)
        # 2. FLUSH: Sends to Postgres to get the ID, but DOES NOT commit permanently.
        db.flush()
        log.debug("database_record_flushed", record_id=record.id, filename=upload_file.filename)

        self_filename = f"{record.id}_{upload_file.filename}"  
        file_path = os.path.join(STORAGE_DIR, self_filename)
        log.debug("starting_file_write", file_path=file_path, record_id=record.id)
        try:
            with open(file_path, "wb") as buffer:
                # shutil.copyfileobj streams the file directly from the HTTP request to the hard drive
                shutil.copyfileobj(upload_file.file, buffer)
            
            log.debug("file_written_to_disk", file_path=file_path, record_id=record.id)
            record.file_path = file_path
            # 5. COMMIT: Now we permanently save everything to the database
            db.commit() 
            db.refresh(record)
            log.info("file_upload_completed_successfully", record_id=record.id, filename=upload_file.filename, file_path=file_path, owner_id=owner_id)
            
            return record
        except Exception as e:
            log.error("file_write_failed", file_path=file_path, record_id=record.id, error=str(e))
            # 6. ROLLBACK: If the file save crashes, we tell Postgres to abort. 
            # The flushed record is instantly erased. No junk data!
            db.rollback()  # Rollback the DB transaction if file saving fails
            raise e
    except Exception as e:
        log.error("process_and_upload_file_failed", filename=upload_file.filename, owner_id=owner_id, error=str(e))
        raise
    finally:
        upload_file.file.close()
        log.debug("upload_file_handle_closed", filename=upload_file.filename)