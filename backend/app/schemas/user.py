from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# what a frontend sends when sigining up
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# What we send back (without the password hash!)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    
    # This is crucial. It tells Pydantic: 
    # "It's okay if the input is a SQLAlchemy object instead of a dictionary. 
    # Just read the attributes directly."
    model_config = ConfigDict(from_attributes=True)

# The shape of JWT token data (claims) 
class Token(BaseModel):
    access_token: str
    token_type: str