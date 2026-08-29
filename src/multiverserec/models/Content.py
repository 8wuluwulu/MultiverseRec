from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, VARCHAR, CheckConstraint
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from multiverserec.core.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class Content(Base):
    __tablename__ = 'content'
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    content_type = Column(VARCHAR(20), CheckConstraint("content_type IN ('book', 'movie')", name="check_content_type"), nullable=False)
    embedding = Column(Vector(384))
    rating = Column(Float, CheckConstraint("rating >= 0 AND rating <= 10", name="check_rating"))
    meta = Column(JSONB, default={})
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    