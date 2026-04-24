from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.upload import UploadResponse
from app.services import upload_service
from app.worker.task import process_data_file
from app.api.deps import DbSession, CurrentUser

router = APIRouter()



@router.post("/", response_model=UploadResponse)
async def upload_data(file: UploadFile , db: DbSession,  current_user: CurrentUser):
    # validation: only allow CSV and JSON files
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(status_code=400, detail="Only CSV and JSON files are allowed")
    
    try:
    # 1. Create a DB record with 'pending' status and get the ID
    # 2. Database Insertion
        record = upload_service.process_and_upload_file(db=db, upload_file=file, owner_id=current_user.id)
        # 2. TRIGGER THE WORKER
        # .delay() is the Celery magic. It does NOT run the function here. 
        # It packages the arguments (record.id, file_path) into JSON, 
        # drops them into Redis, and instantly moves to the next line.
        process_data_file.delay(record_id=record.id, file_path=record.file_path)
        return record
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File storage failed. Upload aborted: {str(e)}")
    

