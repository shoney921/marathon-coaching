from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    target_race = Column(String)
    target_time = Column(String)
    
    training_logs = relationship("TrainingLog", back_populates="user")
    sleep_logs = relationship("SleepLog", back_populates="user")
    race_goals = relationship("RaceGoal", back_populates="user")
    ai_feedbacks = relationship("AIFeedback", back_populates="user") 