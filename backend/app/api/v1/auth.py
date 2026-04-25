from fastapi import APIRouter, Depends, HTTPException, status,Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.services import user_service
from app.core import security
from app.api.deps import DbSession, RateLimitPerIP, rate_limit_endpoint_per_ip
from app.core.config import settings
from app.core.redis import redis_client
import structlog
from pydantic import BaseModel, EmailStr
from app.core.security import generate_reset_token, hash_reset_token


log = structlog.get_logger()
router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_endpoint_per_ip)])
def signup(user: UserCreate, db: DbSession, _rate_limit: RateLimitPerIP):
    log.info("signup_request_received", email=user.email)
    try:
        # 1. Check if email is already taken
        existing_user = user_service.get_user_by_email(db, email=user.email)
        if existing_user:
            log.warning("signup_email_already_exists", email=user.email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")
        
        # Create a user
        new_user = user_service.create_user(db, user)
        log.info("user_signup_successful", user_id=new_user.id, email=user.email)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        log.error("signup_failed", email=user.email, error=str(e))
        raise HTTPException(status_code=500, detail="Signup failed")

@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_endpoint_per_ip)])
async def login(response: Response, db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()):
    log.info("login_request_received", email=form_data.username)
    try:
        access_token, refresh_token, exp_seconds = await user_service.authenticate_user_and_create_session(
            db=db, 
            email=form_data.username, 
            password=form_data.password
        )
        
        # Router only handles HTTP specific tasks (like cookies)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False, 
            samesite="lax",
            max_age=exp_seconds
        )
        
        log.info("login_successful", email=form_data.username)
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        log.error("login_failed", email=form_data.username, error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/refresh", dependencies=[Depends(rate_limit_endpoint_per_ip)])
async def refresh_token(
    # We explicitly look for the 'refresh_token' cookie
    db: DbSession,
    refresh_token: str | None = Cookie(default=None),
):
    log.info("refresh_token_request_received")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    try:
        new_access_token = await user_service.refresh_user_session(db, refresh_token)
        log.info("refresh_token_successful")
        return {"access_token": new_access_token, "token_type": "bearer"}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout", dependencies=[Depends(rate_limit_endpoint_per_ip)])
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None)
):
    log.info("logout_request_received")
    
    # Revoke in Redis
    await user_service.revoke_user_session(refresh_token)
        
    # Clear HTTP cookie
    response.delete_cookie(key="refresh_token")
    log.info("logout_successful")
    
    return {"detail": "Successfully logged out"}
@router.post("/forgot-password", status_code=202)
async def request_password_reset(
    payload: ForgotPasswordRequest,
    request: Request,
    db: DbSession
):
    # 1. Route extracts HTTP data
    client_ip = request.client.host if request.client else "Unknown"
    
    # 2. Route calls Service
    user = user_service.get_user_by_email(db, email=payload.email)
    
    if user:
        plain_token = user_service.create_password_reset_token(db, user, client_ip)
        
        # In the future, your email dispatch logic goes here
        print(f"\n[EMAIL MOCK] Link: http://localhost:3000/reset-password?token={plain_token}\n")
    
    # 3. Route formats HTTP response
    return {"detail": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
async def execute_password_reset(
    payload: ResetPasswordRequest,
    db:DbSession
):
    try:
        # Route passes data to the Service
        user_service.execute_password_reset(db, payload.token, payload.new_password)
        return {"detail": "Password has been successfully reset."}
        
    except ValueError as e:
        # Route catches pure Python errors and translates them into HTTP errors
        raise HTTPException(status_code=400, detail=str(e))