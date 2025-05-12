from fastapi import FastAPI, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from typing import List
from pydantic import BaseModel
import time
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.user import User
from app.models.training import TrainingLog, SleepLog
from app.services.activity_service import ActivityService
from app.services.garmin_service import GarminService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GarminSyncRequest(BaseModel):
    garmin_email: str
    garmin_password: str

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./marathon.db?check_same_thread=False"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 테이블 생성
def init_db():
    Base.metadata.create_all(bind=engine)

app = FastAPI()

# 앱 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup():
    init_db()

@app.get("/dbinit")
async def dbinit():
    init_db()
    return {"message": "Database initialized"}

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 요청/응답 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 요청 시작 시간
    start_time = time.time()
    
    # 요청 정보 로깅
    request_body = None
    try:
        request_body = await request.body()
        if request_body:
            request_body = request_body.decode()
    except:
        pass
    
    logger.info(f"""
    Request:
    Method: {request.method}
    URL: {request.url}
    Headers: {dict(request.headers)}
    Body: {request_body}
    """)
    
    # 응답 처리
    response = await call_next(request)
    
    # 응답 시간 계산
    process_time = time.time() - start_time
    
    # 응답 본문 가져오기
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    # 응답 본문 디코딩
    try:
        response_body = response_body.decode()
    except:
        response_body = str(response_body)
    
    # 응답 정보 로깅
    logger.info(f"""
    Response:
    Status Code: {response.status_code}
    Process Time: {process_time:.2f} seconds
    Body: {response_body}
    """)
    
    # 응답 본문을 다시 설정
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

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

@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@app.post("/users/garmin/{user_id}")
async def update_garmin_sync(user_id: int, garmin_data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 가민 연동 해제인 경우
    if garmin_data.get("garmin_sync_status") == "disconnected":
        user.garmin_email = None
        user.garmin_password = None
        user.garmin_sync_status = "disconnected"
        user.garmin_sync_date = None
        db.commit()
        db.refresh(user)
        return {
            "garmin_sync_status": "disconnected",
            "message": "Garmin sync disconnected successfully"
        }
    
    # 가민 연동인 경우
    garmin_service = GarminService(db)
    if not garmin_service.check_garmin_login(garmin_data["garmin_email"], garmin_data["garmin_password"]):
        raise HTTPException(status_code=400, detail="Garmin login failed")
    
    user.garmin_email = garmin_data["garmin_email"]
    user.garmin_password = garmin_data["garmin_password"]
    user.garmin_sync_date = datetime.now()
    user.garmin_sync_status = "success"
    
    db.commit()
    db.refresh(user)
    return {
        "garmin_sync_date": user.garmin_sync_date,
        "garmin_sync_status": user.garmin_sync_status
    }

@app.post("/auth/login/")
async def login(user_data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data["email"]).first()
    if not user or not user.verify_password(user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user": user, "token": "1234567890"}

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

@app.get("/activities/user/{user_id}")
async def get_activities(user_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.get_activities(user_id)

@app.get("/activities/{activity_id}")
async def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.get_activity(activity_id)

@app.get("/activities/laps/user/{user_id}")
async def get_activities_laps_with_comments(user_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.get_activities_laps_with_comments(user_id)

@app.get("/activities/summary/user/{user_id}")
async def get_activity_summary(user_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.get_activity_summary(user_id)

@app.get("/activities/monthly-summary/user/{user_id}")
async def get_monthly_activity_summary(user_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.get_monthly_activity_summary(user_id)

@app.post("/activities/user/{user_id}") 
async def create_activity(user_id: int, activity_data: dict, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.create_activity(user_id, activity_data)

@app.post("/activities/comments/")
async def create_activity_comment(comment_data: dict, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.create_activity_comment(comment_data)

@app.delete("/activities/comments/{comment_id}")
def delete_activity_comment(comment_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.delete_activity_comment(comment_id)

@app.post("/sync-garmin-activities/{user_id}")
async def sync_garmin_activities(user_id: int, user_data: GarminSyncRequest, db: Session = Depends(get_db)):
    garmin_service = GarminService(db)
    return garmin_service.sync_activities(user_id, user_data.garmin_email, user_data.garmin_password)


## 유틸 함수
#region 유틸
def format_duration(seconds: float) -> str:
    """
    초를 HH:MM:SS.mmm 형식으로 변환
    
    Args:
        seconds: 소요 시간(초)
    
    Returns:
        "HH:MM:SS.mmm" 형식의 문자열
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds_remainder):02d}.{milliseconds:03d}"

def format_pace(seconds_per_km: float) -> str:
    """
    초/km를 분:초.mmm/km 형식으로 변환
    
    Args:
        seconds_per_km: 1km당 소요 시간(초)
    
    Returns:
        "분:초.mmm/km" 형식의 문자열
    """
    minutes = int(seconds_per_km // 60)
    seconds_remainder = seconds_per_km % 60
    seconds = int(seconds_remainder)
    milliseconds = int((seconds_remainder - seconds) * 1000)
    return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

def speed_to_pace(speed_kmh: float) -> str:
    """
    속도(km/h)를 페이스(분:초.mmm/km)로 변환
    
    Args:
        speed_kmh: 시간당 킬로미터(km/h)
    
    Returns:
        "분:초.mmm/km" 형식의 문자열
    """
    if speed_kmh <= 0:
        return "0:00.000"
    seconds_per_km = 3600 / speed_kmh  # 3600초(1시간) / 속도
    return format_pace(seconds_per_km)
#endregion