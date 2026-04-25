from fastapi import APIRouter, UploadFile, File, HTTPException,Request, Security
from app.schemas.upload import UploadResponse
from app.services import upload_service
from app.worker.task import process_data_file
from app.api.deps import DbSession, CurrentUser, RateLimitEndpointPerIP, require_permissions
from app.models.upload import DataUpload
from typing import Annotated
import structlog
from app.models.user import User
from app.core.cache import cache_response, invalidate_user_cache
log = structlog.get_logger()
router = APIRouter()



@router.post("/", response_model=UploadResponse)
async def upload_data(file: UploadFile , db: DbSession,  current_user: CurrentUser,_rate_limit : RateLimitEndpointPerIP):
    log.info("upload_request_received", filename=file.filename, user_id=current_user.db_user.id)
    try:
        # validation: only allow CSV and JSON files
        if not file.filename.endswith(('.csv', '.json')):
            log.warning("invalid_file_type_rejected", filename=file.filename, user_id=current_user.db_user.id)
            raise HTTPException(status_code=400, detail="Only CSV and JSON files are allowed")
        
        log.debug("file_validation_passed", filename=file.filename, size=file.size)
        # 1. Create a DB record with 'pending' status and get the ID
        # 2. Database Insertion
        record = upload_service.process_and_upload_file(db=db, upload_file=file, owner_id=current_user.db_user.id)
        await invalidate_user_cache(current_user.db_user.id)
        log.info("file_saved_sending_to_worker", record_id=record.id, filename=file.filename, file_path=record.file_path)
        # 2. TRIGGER THE WORKER
        # .delay() is the Celery magic. It does NOT run the function here. 
        # It packages the arguments (record.id, file_path) into JSON, 
        # drops them into Redis, and instantly moves to the next line.
        process_data_file.delay(record_id=record.id, file_path=record.file_path)
        log.debug("worker_task_triggered", record_id=record.id)
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("upload_transaction_failed", error=str(e), user_id=current_user.db_user.id, filename=file.filename)
        raise HTTPException(status_code=500, detail=f"File storage failed. Upload aborted: {str(e)}")
    

@router.get("/", response_model=list[UploadResponse])
@cache_response(ttl_seconds=300) # Snap the cache on!
async def get_user_uploads(
    request: Request, # MUST be included for the decorator to read the path
    db: DbSession,
    current_user: CurrentUser
):
    """Fetches all uploads for the logged-in user."""
    # A standard, potentially slow DB query
    records = db.query(DataUpload).filter(DataUpload.owner_id == current_user.db_user.id).all()
    return records

@router.delete("/{upload_id}", status_code=204)
async def delete_upload(
    upload_id: int,
    db: DbSession,
   current_user: User = Security(require_permissions, scopes=["uploads:delete"])
):

    # Find the record
    record = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")
        
    # Delete from DB
    db.delete(record)
    db.commit()
    
    # Optionally: Invalidate the user's cache so the deleted item disappears from their GET list!
    await invalidate_user_cache(current_user.db_user.id)
    
    return None