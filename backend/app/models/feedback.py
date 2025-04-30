from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .user import Base

class AIFeedback(Base):
    __tablename__ = "ai_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime)
    status = Column(String)  # pending, completed, failed
    feedback_data = Column(JSON)  # AI 코칭 결과를 JSON으로 저장
    
    user = relationship("User", back_populates="ai_feedbacks") 