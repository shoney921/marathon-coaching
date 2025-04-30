from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from models.user import User
from models.training import TrainingLog, SleepLog, RaceGoal
from models.feedback import AIFeedback
from tasks.coaching import request_coaching

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./marathon.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/training-logs/")
async def create_training_log(log_data: dict, db: Session = Depends(get_db)):
    log = TrainingLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@app.post("/sleep-logs/")
async def create_sleep_log(log_data: dict, db: Session = Depends(get_db)):
    log = SleepLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@app.post("/request-coaching/{user_id}")
async def request_ai_coaching(user_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # AI 피드백 요청 생성
    feedback = AIFeedback(
        user_id=user_id,
        created_at=datetime.now(),
        status="pending"
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    # Celery 태스크 실행
    background_tasks.add_task(request_coaching, user_id, feedback.id)
    
    return {"message": "Coaching request submitted", "feedback_id": feedback.id}

@app.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(AIFeedback).filter(AIFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback 