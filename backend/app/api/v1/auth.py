from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.services import user_service
from app.core import security
from app.api.deps import DbSession, DbSession
from app.core.config import settings
from app.core.redis import redis_client

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: DbSession):
    # 1. Check if email is already taken
    existing_user = user_service.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")
    
    # Create a user
    new_user = user_service.create_user(db, user)
    return new_user

@router.post("/login", response_model=Token)
async def login(response: Response, db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm expects 'username' and 'password' from the frontend (as form data, not JSON)

    # Find user (FastAPI calls the field 'username', but we map it to our 'email')
    user = user_service.get_user_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials." )
    
    # Verify password
    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials." )
    
    # Generate JWT token
    access_token = security.create_access_token(data={"sub": str(user.id), "email": (user.email), "is_active": (user.is_active)})
    refresh_token = security.create_refresh_token()
    # 2. Store the Refresh Token in Redis (Whitelist)
    # Key: refresh_token:<the_token_string>, Value: user_id
    redis_key = f"refresh_token:{refresh_token}"
    expiration_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis_client.setex(name=redis_key, time=expiration_seconds, value=str(user.id))
    # 3. Set the HttpOnly Cookie
    # HttpOnly=True prevents XSS attacks (React cannot read it)
    # Secure=True ensures it only sends over HTTPS (disable temporarily if testing without localhost HTTPS)
    # SameSite='lax' protects against CSRF attacks
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False, # Set to True in production!
        samesite="lax",
        max_age=expiration_seconds
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh")
async def refresh_token(
    # We explicitly look for the 'refresh_token' cookie
    refresh_token: str | None = Cookie(default=None)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    redis_key = f"refresh_token:{refresh_token}"
    
    # 1. Check if the token exists in Redis
    user_id = await redis_client.get(redis_key)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    # 2. Generate a NEW Access Token
    new_access_token = security.create_access_token(data={"sub": user_id})
    
    # (Optional Enterprise Step: Token Rotation)
    # You could delete the old refresh token here and issue a new one to prevent replay attacks.
    # For now, we keep the session alive until the 7 days expire.
    
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None)
):
    if refresh_token:
        # 1. Delete from Redis (Revoke access)
        await redis_client.delete(f"refresh_token:{refresh_token}")
        
    # 2. Instruct the browser to delete the cookie
    response.delete_cookie(key="refresh_token")
    
    return {"detail": "Successfully logged out"}