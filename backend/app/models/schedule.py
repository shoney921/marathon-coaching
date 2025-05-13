from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class TrainingSchedule(Base):
    __tablename__ = "training_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    schedule_datetime = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # 훈련, 휴식, 대회 등
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    user = relationship("User", back_populates="training_schedules")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "datetime": self.schedule_datetime.isoformat(),
            "description": self.description,
            "type": self.type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 