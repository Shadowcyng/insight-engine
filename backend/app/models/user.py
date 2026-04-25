from sqlalchemy import Text, Column, Integer, String, Boolean, DateTime, func, ForeignKey, Table
from app.db.base import Base
from sqlalchemy.orm import relationship

# 1. Junction table for Many-to-Many relationship
role_permissions = Table(
   'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

# 2. The Permission table (e.g., "uploads:delete")
class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)

# 3. The Role table (e.g., "Manager")
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    permissions = relationship("Permission", secondary=role_permissions)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # We only store the bcrypt hash, never the actual password
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    role = relationship(Role)

class PasswordReset(Base):
    """Enterprise audit table for password reset events."""
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Cryptographically secure hash of the token
    hashed_token = Column(String, unique=True, index=True, nullable=False)
    
    # Audit trail
    request_ip = Column(String, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True) # Marks it as used
    
    user = relationship("User")