from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_command_id = Column(
        Integer,
        ForeignKey("prediction_commands.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    actual_result = Column(String(20), nullable=False)  # FAIL, PASS, NOT_RUN
    notes = Column(Text, nullable=True)
    submitted_by = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    command = relationship("PredictionCommand", back_populates="feedback")
