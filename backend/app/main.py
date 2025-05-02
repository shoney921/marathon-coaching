from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from typing import List

from app.models.user import User
from app.models.training import TrainingLog, SleepLog, RaceGoal
from app.models.feedback import AIFeedback
from tasks.coaching import request_coaching

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./marathon.db?check_same_thread=False"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 테이블 생성
def init_db():
    Base.metadata.create_all(bind=engine)

app = FastAPI()

# 앱 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup():
    init_db()

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    # 비밀번호 해시화
    hashed_password = User.get_password_hash(user_data.pop("password"))
    user_data["hashed_password"] = hashed_password
    
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/", response_model=List[dict])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": user.id, 
             "username": user.username, 
             "email": user.email,
             "age": user.age,
             "weight": user.weight,
             "height": user.height,
             "target_race": user.target_race,
             "target_time": user.target_time} for user in users]

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
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

@app.post("/auth/login/")
async def login(user_data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data["email"]).first()
    if not user or not user.verify_password(user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    print("## user")
    print(user)
    return {"message": "Login successful", "user": user}


@app.post("/auth/register/")
async def register(user_data: dict, db: Session = Depends(get_db)):

    print("## user_data")
    print(user_data)

    # 비밀번호 해시화
    hashed_password = User.get_password_hash(user_data.pop("password"))
    user_data["hashed_password"] = hashed_password
    
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registration successful", "user_id": user.id}

