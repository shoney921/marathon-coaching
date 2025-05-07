from celery import Celery
import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.feedback import AIFeedback

# Celery 설정
celery_app = Celery('coaching', broker='redis://redis:6379/0')

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./marathon.db?check_same_thread=False"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task
def request_coaching(user_id: int, feedback_id: int):
    db = SessionLocal()
    try:
        # MCP 서버에 요청 보내기
        mcp_url = "http://mcp-server:8000/analyze"
        response = requests.post(mcp_url, json={"user_id": user_id})
        
        if response.status_code == 200:
            # 성공적으로 응답을 받았을 때
            feedback = db.query(AIFeedback).filter(AIFeedback.id == feedback_id).first()
            if feedback:
                feedback.status = "completed"
                feedback.feedback_data = response.json()
                db.commit()
        else:
            # 실패했을 때
            feedback = db.query(AIFeedback).filter(AIFeedback.id == feedback_id).first()
            if feedback:
                feedback.status = "failed"
                db.commit()
    except Exception as e:
        # 예외 발생 시
        feedback = db.query(AIFeedback).filter(AIFeedback.id == feedback_id).first()
        if feedback:
            feedback.status = "failed"
            db.commit()
    finally:
        db.close() 