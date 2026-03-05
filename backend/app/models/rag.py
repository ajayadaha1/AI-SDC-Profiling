from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from ..database import Base

# pgvector Vector type - imported conditionally
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


class RAGNormalizationExample(Base):
    __tablename__ = "rag_normalization_examples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_name = Column(String(100), nullable=False, index=True)
    raw_value = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=False)
    embedding = Column(Vector(3072), nullable=True) if Vector else Column(Text, nullable=True)
    source = Column(String(50), nullable=False, default="seed")  # seed, feedback, manual
    confidence = Column(Float, nullable=False, default=1.0)
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
