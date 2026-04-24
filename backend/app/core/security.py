import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
import secrets


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if the provided plain password matches the stored hashed password.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """
    Hash the password using bcrypt and return the hash.
    """
    password_bytes = password.encode('utf-8')
    # generate random salt
    salt = bcrypt.gensalt()
    # 3. Hash the password with the salt
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # 4. Convert back to string so Postgres can store it
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    # 1. Copy the data so we don't mutate the original dictionary
    to_encode = data.copy()

    # 2. Set the expiration time (the 'exp' claim is a JWT standard)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    # 3. Cryptographically sign the token using our secret key
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

def create_refresh_token() -> str:
    """Generates a secure, random opaque token for session management."""
    return secrets .token_urlsafe(64)