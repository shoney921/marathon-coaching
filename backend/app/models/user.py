from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    age = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    target_race = Column(String)
    target_time = Column(String)
    
    training_logs = relationship("TrainingLog", back_populates="user")
    sleep_logs = relationship("SleepLog", back_populates="user")
    race_goals = relationship("RaceGoal", back_populates="user")
    ai_feedbacks = relationship("AIFeedback", back_populates="user")
    
    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password) 