from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, generate_reset_token, hash_reset_token, create_access_token, create_refresh_token, verify_password
import structlog
from app.models.user import User, PasswordReset
from datetime import datetime, timezone, timedelta
from app.core.redis import redis_client
from app.core.config import settings

log = structlog.get_logger()

def get_user_by_email(db: Session, email: str) -> User | None:
    log.debug("fetching_user_by_email", email=email)
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            log.debug("user_found", user_id=user.id, email=email)
        else:
            log.debug("user_not_found", email=email)
        return user
    except Exception as e:
        log.error("get_user_by_email_failed", email=email, error=str(e))
        raise

def create_user(db: Session, user: UserCreate) -> User:
    log.info("creating_new_user", email=user.email)
    try:
        # 1. Hash the plain text password
        hashed_password = get_password_hash(user.password)
        log.debug("password_hashed", email=user.email)
        # 2. Create the DB instance
        db_user = User(email=user.email, hashed_password=hashed_password)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        log.info("user_created_successfully", user_id=db_user.id, email=user.email)
        return db_user
    except Exception as e:
        log.error("create_user_failed", email=user.email, error=str(e))
        db.rollback()
        raise

async def authenticate_user_and_create_session(db: Session, email: str, password: str) -> tuple[str, str, int]:
    # Find and verify user
    user = get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        log.warning("auth_failed", email=email)
        raise ValueError("Invalid credentials.")
        
    # Build full JWT payload
    user_scopes = [perm.name for perm in user.role.permissions] if user.role and user.role.permissions else []
    jwt_data = {
        "sub": str(user.id), 
        "email": user.email, 
        "is_active": user.is_active,
        "scopes": user_scopes
    }
    
    # Generate tokens
    access_token = create_access_token(data=jwt_data)
    refresh_token = create_refresh_token()
    
    # Store session in Redis
    expiration_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    redis_key = f"refresh_token:{refresh_token}"
    await redis_client.setex(name=redis_key, time=expiration_seconds, value=str(user.id))
    
    return access_token, refresh_token, expiration_seconds, user

async def refresh_user_session(db: Session, refresh_token: str) -> str:
    redis_key = f"refresh_token:{refresh_token}"
    user_id = await redis_client.get(redis_key)
    
    if not user_id:
        log.warning("invalid_refresh_token")
        raise ValueError("Invalid or expired refresh token")
        
    # THE BUG FIX: We must fetch the user from the DB again 
    # to rebuild the scopes, otherwise RBAC breaks after 15 minutes!
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise ValueError("User no longer exists")
        
    user_scopes = [perm.name for perm in user.role.permissions] if user.role and user.role.permissions else []
    
    new_jwt_data = {
        "sub": str(user.id), 
        "email": user.email, 
        "is_active": user.is_active,
        "scopes": user_scopes
    }
    
    token =  create_access_token(data=new_jwt_data)
    return token, user


async def revoke_user_session(refresh_token: str) -> None:
    if refresh_token:
        await redis_client.delete(f"refresh_token:{refresh_token}")

def create_password_reset_token(db: Session, user: User, client_ip: str) -> str:
    """Generates a token, hashes it, saves the audit record, and returns the plain text."""
    plain_token = generate_reset_token()
    hashed_token = hash_reset_token(plain_token)
    
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    reset_record = PasswordReset(
        user_id=user.id,
        hashed_token=hashed_token,
        request_ip=client_ip,
        expires_at=expires
    )
    db.add(reset_record)
    db.commit()
    
    # We return the plain token so the router can send the email
    return plain_token

def execute_password_reset(db: Session, plain_token: str, new_password: str) -> bool:
    """Validates the token and updates the user's password atomically."""
    hashed_incoming_token = hash_reset_token(plain_token)
    
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.hashed_token == hashed_incoming_token
    ).first()
    
    if not reset_record:
        raise ValueError("Invalid token")
        
    now = datetime.now(timezone.utc)
    if reset_record.expires_at.replace(tzinfo=timezone.utc) < now:
        raise ValueError("Token has expired")
        
    if reset_record.consumed_at is not None:
        raise ValueError("Token has already been used")
        
    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user:
        raise ValueError("User no longer exists")
        
    # Apply updates
    user.hashed_password = get_password_hash(new_password)
    reset_record.consumed_at = now
    
    db.commit()
    return True