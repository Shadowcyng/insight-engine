from sqlalchemy import Column, Integer, String, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.user import User

class DataUpload(Base):
    __tablename__ = "data_uploads"

    id = Column(Integer, primary_key=True, index=True,)
    # The crucial link: Every upload must have an owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending") # pending, processing, completed, failed
    # NEW: We allow this to be nullable initially because we create the DB 
    # record *before* the file finishes saving to disk.
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # NEW: Store the AI's generated response
    ai_summary = Column(Text, nullable=True)
    # This lets us do record.owner to fetch the user object directly
    owner = relationship(User)