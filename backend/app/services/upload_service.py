from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.upload import DataUpload
from utils.constants import STORAGE_DIR
import os
import shutil

# Our local "S3 Bucket" equivalent
os.makedirs(STORAGE_DIR, exist_ok=True)


def process_and_upload_file(db: Session,upload_file: UploadFile, owner_id: int)-> DataUpload:
    # Step 1: Prepare the record
    record = DataUpload(filename=upload_file.filename, status="pending", owner_id=owner_id)
    # Step 2: Save the file to disk
    db.add(record)
    # 2. FLUSH: Sends to Postgres to get the ID, but DOES NOT commit permanently.
    db.flush()

    self_filename = f"{record.id}_{upload_file.filename}"  
    file_path = os.path.join(STORAGE_DIR, self_filename)
    try:
        with open(file_path, "wb") as buffer:
            # shutil.copyfileobj streams the file directly from the HTTP request to the hard drive
            shutil.copyfileobj(upload_file.file, buffer)
        
        record.file_path = file_path
        # 5. COMMIT: Now we permanently save everything to the database
        db.commit() 
        db.refresh(record)
        
        return record
    except Exception as e:
        print(f"Error occurred while saving file: {e}")
        # 6. ROLLBACK: If the file save crashes, we tell Postgres to abort. 
        # The flushed record is instantly erased. No junk data!
        db.rollback()  # Rollback the DB transaction if file saving fails
        raise e
    finally:
        upload_file.file.close()