from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, func
from app.db.base import Base 

class CanvasLayout(Base):
    __tablename__ = "canvas_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="Untitled Graph")
    
    # Minor comment: Stores the full React Flow state
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    
    # Minor comment: Metadata for the Insight Engine
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
