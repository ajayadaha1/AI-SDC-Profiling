from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    # Parsed failure profile
    symptom_text = Column(Text, nullable=False)
    parsed_failure_type = Column(String(64), nullable=True, index=True)
    parsed_mce_bank = Column(Integer, nullable=True)
    parsed_mce_code = Column(String(20), nullable=True)
    parsed_thermal_state = Column(String(20), nullable=True)
    parsed_boot_stage = Column(String(20), nullable=True)
    parsed_confidence = Column(Float, nullable=True)
    parsed_profile_json = Column(JSONB, nullable=True)

    # Search metadata
    match_tier = Column(Integer, nullable=True)
    similar_parts_count = Column(Integer, nullable=True)

    # Full prediction result
    prediction_json = Column(JSONB, nullable=False)

    # Model tracking
    model_version = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    commands = relationship("PredictionCommand", back_populates="prediction", cascade="all, delete-orphan", order_by="PredictionCommand.rank")


class PredictionCommand(Base):
    __tablename__ = "prediction_commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True)

    rank = Column(Integer, nullable=False)
    command = Column(String(256), nullable=False)
    confidence = Column(Float, nullable=False)
    fail_rate_on_similar = Column(String(50), nullable=True)
    estimated_time_to_fail = Column(String(50), nullable=True)
    reasoning = Column(Text, nullable=True)

    prediction = relationship("Prediction", back_populates="commands")
    feedback = relationship("Feedback", back_populates="command", uselist=False)
