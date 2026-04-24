from pydantic import BaseModel, ConfigDict
from datetime import datetime

# We define exactly what the React frontend will receive after a successful upload.
class UploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime
    
    # This is crucial. It tells Pydantic: 
    # "It's okay if the input is a SQLAlchemy object instead of a dictionary. 
    # Just read the attributes directly."
    model_config = ConfigDict(from_attributes=True)
    