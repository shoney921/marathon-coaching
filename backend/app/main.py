from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import logging
from typing import List
from garminconnect import Garmin
from pydantic import BaseModel
import os
import time
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.user import User
from app.models.training import TrainingLog, SleepLog, RaceGoal
from app.models.activity import Activity, ActivityComment, ActivitySplit
from app.services.activity_service import ActivityService
# from tasks.coaching import request_coaching

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
    email: str
    password: str

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
    # 문자열 날짜를 datetime 객체로 변환
    if isinstance(log_data.get('date'), str):
        log_data['date'] = datetime.fromisoformat(log_data['date'])
    
    log = TrainingLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@app.get("/training-logs/user/{user_id}")
async def get_training_logs(user_id: int, db: Session = Depends(get_db)):
    logs = db.query(TrainingLog).filter(TrainingLog.user_id == user_id).all()
    return logs

@app.post("/sleep-logs/")
async def create_sleep_log(log_data: dict, db: Session = Depends(get_db)):
    log = SleepLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

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

@app.post("/activities/comments/")
async def create_activity_comment(comment_data: dict, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.create_activity_comment(comment_data)

@app.delete("/activities/comments/{comment_id}")
def delete_activity_comment(comment_id: int, db: Session = Depends(get_db)):
    activity_service = ActivityService(db)
    return activity_service.delete_activity_comment(comment_id)

def parse_garmin_datetime(date_str: str) -> datetime:
    """
    가민에서 제공하는 날짜 문자열을 datetime 객체로 변환
    
    Args:
        date_str: 가민 날짜 문자열 (예: '2025-05-07T22:20:30.0')
    
    Returns:
        datetime 객체
    """
    try:
        # 마지막의 .0을 제거하고 파싱
        if date_str.endswith('.0'):
            date_str = date_str[:-2]
        return datetime.fromisoformat(date_str)
    except ValueError as e:
        logger.error(f"Error parsing date {date_str}: {str(e)}")
        raise

@app.post("/process-activity-splits/{activity_id}")
async def process_activity_splits(activity_id: int, user_data: GarminSyncRequest, db: Session = Depends(get_db)):
    try:
        # Garmin Connect 클라이언트 초기화 및 로그인
        client = Garmin(user_data.email, user_data.password)
        client.login()

        logger.info(f"activity_id {activity_id}")        
        logger.info(f"activity_id type {type(activity_id)}")
        # 활동이 존재하는지 확인
        activity = db.query(Activity).filter(Activity.activity_id == str(activity_id)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        logger.info(f"activity {str(activity.activity_id)}")
        
        # ActivityService를 사용하여 랩 데이터 처리
        activity_service = ActivityService(db)
        activity_service.process_activity_splits(client, str(activity.activity_id))
        return {"message": "Activity splits processed successfully"}
        
    except Exception as e:
        logger.error(f"Error in process_activity_splits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/sync-garmin-activities/{user_id}")
async def sync_garmin_activities(user_id: int, user_data: GarminSyncRequest, db: Session = Depends(get_db)):
    try:
        logger.info("Starting Garmin sync process")
        
        # Garmin Connect 클라이언트 초기화
        client = Garmin(user_data.email, user_data.password)
        print(user_data.email)
        # 로그인
        logger.info("Attempting to login to Garmin Connect")
        try:
            client.login()
            logger.info("Successfully logged in to Garmin Connect")
        except Exception as e:
            logger.error(f"Failed to login to Garmin Connect: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to login to Garmin Connect")
        
        # 최근 활동 가져오기 (최근 10개)
        logger.info("Fetching recent activities")
        try:
            activities = client.get_activities(0, 100)
            logger.info(f"Successfully fetched activities: {activities}")
        except Exception as e:
            logger.error(f"Failed to fetch activities: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch activities from Garmin Connect")
        
        if not activities:
            logger.info("No activities found")
            return {"message": "No activities found"}
        
        logger.info(f"Found {len(activities)} activities")
        synced_count = 0
        
        for activity_data in activities:
            print("## activity_data")
            print(activity_data)
            try:
                # 이미 저장된 활동인지 확인
                existing_activity = db.query(Activity).filter(
                    Activity.activity_id == activity_data.get('activityId')
                ).first()
                
                if existing_activity:
                    logger.info(f"Activity {activity_data.get('activityId')} already exists, skipping")
                    continue
                
                # 심박수 구간 시간
                hr_zones = {
                    'zone_1': activity_data.get('hrTimeInZone_1', 0),
                    'zone_2': activity_data.get('hrTimeInZone_2', 0),
                    'zone_3': activity_data.get('hrTimeInZone_3', 0),
                    'zone_4': activity_data.get('hrTimeInZone_4', 0),
                    'zone_5': activity_data.get('hrTimeInZone_5', 0)
                }
                
                # 파워 구간 시간
                power_zones = {
                    'zone_1': activity_data.get('powerTimeInZone_1', 0),
                    'zone_2': activity_data.get('powerTimeInZone_2', 0),
                    'zone_3': activity_data.get('powerTimeInZone_3', 0),
                    'zone_4': activity_data.get('powerTimeInZone_4', 0),
                    'zone_5': activity_data.get('powerTimeInZone_5', 0)
                }
                
                # 날짜 문자열을 datetime 객체로 변환
                try:
                    start_time_local = datetime.fromisoformat(activity_data.get('startTimeLocal'))
                    start_time_gmt = datetime.fromisoformat(activity_data.get('startTimeGMT'))
                    end_time_gmt = datetime.fromisoformat(activity_data.get('endTimeGMT'))
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting dates for activity {activity_data.get('activityId')}: {str(e)}")
                    continue
                
                # Activity 모델에 맞는 데이터 구성
                activity = Activity(
                    activity_id=activity_data.get('activityId'),
                    activity_name=activity_data.get('activityName'),
                    user_id=user_id,
                    start_time_local=start_time_local,
                    start_time_gmt=start_time_gmt,
                    end_time_gmt=end_time_gmt,
                    activity_type=activity_data.get('activityType'),
                    event_type=activity_data.get('eventType'),
                    distance=activity_data.get('distance'),
                    duration=activity_data.get('duration'),
                    elapsed_duration=activity_data.get('elapsedDuration'),
                    moving_duration=activity_data.get('movingDuration'),
                    elevation_gain=activity_data.get('elevationGain'),
                    elevation_loss=activity_data.get('elevationLoss'),
                    min_elevation=activity_data.get('minElevation'),
                    max_elevation=activity_data.get('maxElevation'),
                    elevation_corrected=activity_data.get('elevationCorrected', False),
                    average_speed=activity_data.get('averageSpeed'),
                    max_speed=activity_data.get('maxSpeed'),
                    start_latitude=activity_data.get('startLatitude'),
                    start_longitude=activity_data.get('startLongitude'),
                    end_latitude=activity_data.get('endLatitude'),
                    end_longitude=activity_data.get('endLongitude'),
                    average_hr=activity_data.get('averageHR'),
                    max_hr=activity_data.get('maxHR'),
                    hr_time_in_zones=hr_zones,
                    avg_power=activity_data.get('avgPower'),
                    max_power=activity_data.get('maxPower'),
                    power_time_in_zones=power_zones,
                    aerobic_training_effect=activity_data.get('aerobicTrainingEffect'),
                    anaerobic_training_effect=activity_data.get('anaerobicTrainingEffect'),
                    training_effect_label=activity_data.get('trainingEffectLabel'),
                    vo2max_value=activity_data.get('vO2MaxValue'),
                    average_cadence=activity_data.get('averageRunningCadenceInStepsPerMinute'),
                    max_cadence=activity_data.get('maxRunningCadenceInStepsPerMinute'),
                    avg_vertical_oscillation=activity_data.get('avgVerticalOscillation'),
                    avg_ground_contact_time=activity_data.get('avgGroundContactTime'),
                    avg_stride_length=activity_data.get('avgStrideLength'),
                    calories=activity_data.get('calories'),
                    water_estimated=activity_data.get('waterEstimated'),
                    activity_training_load=activity_data.get('activityTrainingLoad'),
                    moderate_intensity_minutes=activity_data.get('moderateIntensityMinutes'),
                    vigorous_intensity_minutes=activity_data.get('vigorousIntensityMinutes'),
                    steps=activity_data.get('steps'),
                    time_zone_id=activity_data.get('timeZoneId'),
                    sport_type_id=activity_data.get('sportTypeId'),
                    device_id=activity_data.get('deviceId'),
                    manufacturer=activity_data.get('manufacturer'),
                    lap_count=activity_data.get('lapCount'),
                    privacy=activity_data.get('privacy'),
                    favorite=activity_data.get('favorite', False),
                    manual_activity=activity_data.get('manualActivity', False)
                )
                
                db.add(activity)
                db.flush()  # ID를 얻기 위해 flush
                
                # 랩 데이터 가져오기
                process_activity_splits(client, activity.activity_id, db, logger)
                
                synced_count += 1
                logger.info(f"Successfully added activity {activity_data.get('activityId')}")
                
            except Exception as e:
                logger.error(f"Error processing activity {activity_data.get('activityId')}: {str(e)}")
                continue
        
        db.commit()
        logger.info(f"Sync completed. Synced {synced_count} activities")
        return {
            "message": f"Successfully synced {synced_count} activities",
            "total_activities": len(activities)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during sync process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))