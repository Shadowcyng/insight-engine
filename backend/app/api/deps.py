from typing import Annotated
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.models.user import User
from app.api.rate_limit import RateLimiter
from fastapi.security import SecurityScopes
from dataclasses import dataclass

@dataclass
class AuthenticatedUser:
    db_user: User
    scopes: list[str]

# This tells Swagger UI where the login endpoint is, 
# so the "Authorize" button knows where to send the credentials.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 1. Create a reusable type alias for the DB Session dependency.
# This makes your route files incredibly clean later.

DbSession = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(token: TokenDep, db: DbSession) -> AuthenticatedUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        token_scopes: list = payload.get("scopes",[])
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    return AuthenticatedUser(db_user=user, scopes=token_scopes)

# 2. We can even create a type alias for the Current User!
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]

# ===== RATE LIMITING STRATEGIES =====
# IP-based rate limiting only (works without authentication)

# Per-IP globally: 100 requests per 60 seconds from each IP
rate_limit_per_ip = RateLimiter(
    max_requests=100,
    window_seconds=60,
    key_strategy="per_ip"
)
RateLimitPerIP = Annotated[bool, Depends(rate_limit_per_ip)]

# Per-endpoint per-IP: 20 requests per 60 seconds per endpoint per IP
rate_limit_endpoint_per_ip = RateLimiter(
    max_requests=20,
    window_seconds=60,
    key_strategy="endpoint_per_ip"
)
RateLimitEndpointPerIP = Annotated[bool, Depends(rate_limit_endpoint_per_ip)]

# Legacy alias for backward compatibility
RateLimit = RateLimitEndpointPerIP

# CUSTOM strategy: Rate limit by API key (example)
# You can define any custom key generation function
def custom_api_key_limiter(req, user):
    api_key = req.headers.get("X-API-Key", "anonymous")
    return f"rate_limit:api_key:{api_key}"

rate_limit_custom = RateLimiter(
    max_requests=1000,
    window_seconds=3600,  # 1 hour
    key_func=custom_api_key_limiter
)
RateLimitCustom = Annotated[bool, Depends(rate_limit_custom)]

def require_permissions(
    security_scopes: SecurityScopes, 
    auth_data: AuthenticatedUser = Security(get_current_user) # 4. Receive the dataclass
) -> User:
    """The Gatekeeper: Compares route requirements against user's token scopes."""
    
    if not security_scopes.scopes:
        return auth_data.db_user
        
    for required_scope in security_scopes.scopes:
        # 5. Safely check the explicitly typed list
        if required_scope not in auth_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_scope}"
            )
            
    # 6. Return just the SQLAlchemy User model to the final API route
    # so your routes don't have to change their signatures!
    return auth_data.db_user