from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .user import Base

class TrainingLog(Base):
    __tablename__ = "training_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    distance = Column(Float)  # km
    duration = Column(Float)  # minutes
    pace = Column(Float)  # min/km
    heart_rate = Column(Float)
    notes = Column(String)
    
    user = relationship("User", back_populates="training_logs")

class SleepLog(Base):
    __tablename__ = "sleep_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    duration = Column(Float)  # hours
    quality = Column(Integer)  # 1-5 scale
    notes = Column(String)
    
    user = relationship("User", back_populates="sleep_logs")

class RaceGoal(Base):
    __tablename__ = "race_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    race_name = Column(String)
    race_date = Column(DateTime)
    target_time = Column(String)
    current_pace = Column(Float)
    target_pace = Column(Float)
    
    user = relationship("User", back_populates="race_goals") 