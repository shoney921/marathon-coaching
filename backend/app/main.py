from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import logging
from typing import List
from garminconnect import Garmin
from pydantic import BaseModel

from app.models.base import Base
from app.models.user import User
from app.models.training import TrainingLog, SleepLog, RaceGoal
from app.models.feedback import AIFeedback
from app.models.activity import Activity
from tasks.coaching import request_coaching

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

@app.post("/activities/")
async def create_activity(activity_data: dict, db: Session = Depends(get_db)):
    # 문자열 날짜를 datetime 객체로 변환
    if isinstance(activity_data.get('startTimeLocal'), str):
        activity_data['start_time_local'] = datetime.fromisoformat(activity_data['startTimeLocal'])
    if isinstance(activity_data.get('startTimeGMT'), str):
        activity_data['start_time_gmt'] = datetime.fromisoformat(activity_data['startTimeGMT'])
    if isinstance(activity_data.get('endTimeGMT'), str):
        activity_data['end_time_gmt'] = datetime.fromisoformat(activity_data['endTimeGMT'])
    
    # JSON 필드 처리
    activity_data['activity_type'] = activity_data.pop('activityType')
    activity_data['event_type'] = activity_data.pop('eventType')
    activity_data['privacy'] = activity_data.pop('privacy')
    
    # 심박수 구간 시간
    hr_zones = {
        'zone_1': activity_data.pop('hrTimeInZone_1', 0),
        'zone_2': activity_data.pop('hrTimeInZone_2', 0),
        'zone_3': activity_data.pop('hrTimeInZone_3', 0),
        'zone_4': activity_data.pop('hrTimeInZone_4', 0),
        'zone_5': activity_data.pop('hrTimeInZone_5', 0)
    }
    activity_data['hr_time_in_zones'] = hr_zones
    
    # 파워 구간 시간
    power_zones = {
        'zone_1': activity_data.pop('powerTimeInZone_1', 0),
        'zone_2': activity_data.pop('powerTimeInZone_2', 0),
        'zone_3': activity_data.pop('powerTimeInZone_3', 0),
        'zone_4': activity_data.pop('powerTimeInZone_4', 0),
        'zone_5': activity_data.pop('powerTimeInZone_5', 0)
    }
    activity_data['power_time_in_zones'] = power_zones
    
    # 컬럼명 변환
    column_mapping = {
        'activityId': 'activity_id',
        'activityName': 'activity_name',
        'distance': 'distance',
        'duration': 'duration',
        'elapsedDuration': 'elapsed_duration',
        'movingDuration': 'moving_duration',
        'elevationGain': 'elevation_gain',
        'elevationLoss': 'elevation_loss',
        'averageSpeed': 'average_speed',
        'maxSpeed': 'max_speed',
        'startLatitude': 'start_latitude',
        'startLongitude': 'start_longitude',
        'endLatitude': 'end_latitude',
        'endLongitude': 'end_longitude',
        'calories': 'calories',
        'averageHR': 'average_hr',
        'maxHR': 'max_hr',
        'averageRunningCadenceInStepsPerMinute': 'average_cadence',
        'maxRunningCadenceInStepsPerMinute': 'max_cadence',
        'steps': 'steps',
        'timeZoneId': 'time_zone_id',
        'sportTypeId': 'sport_type_id',
        'avgPower': 'avg_power',
        'maxPower': 'max_power',
        'aerobicTrainingEffect': 'aerobic_training_effect',
        'anaerobicTrainingEffect': 'anaerobic_training_effect',
        'avgVerticalOscillation': 'avg_vertical_oscillation',
        'avgGroundContactTime': 'avg_ground_contact_time',
        'avgStrideLength': 'avg_stride_length',
        'vO2MaxValue': 'vo2max_value',
        'deviceId': 'device_id',
        'minElevation': 'min_elevation',
        'maxElevation': 'max_elevation',
        'manufacturer': 'manufacturer',
        'lapCount': 'lap_count',
        'waterEstimated': 'water_estimated',
        'trainingEffectLabel': 'training_effect_label',
        'activityTrainingLoad': 'activity_training_load',
        'moderateIntensityMinutes': 'moderate_intensity_minutes',
        'vigorousIntensityMinutes': 'vigorous_intensity_minutes',
        'favorite': 'favorite',
        'manualActivity': 'manual_activity',
        'elevationCorrected': 'elevation_corrected'
    }
    
    # 데이터 변환
    converted_data = {}
    for old_key, new_key in column_mapping.items():
        if old_key in activity_data:
            converted_data[new_key] = activity_data[old_key]
    
    activity = Activity(**converted_data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity



@app.get("/activities/", response_model=List[dict])
async def get_activities(db: Session = Depends(get_db)):
    activities = db.query(Activity).all()
    return activities

@app.get("/activities/{activity_id}")
async def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

class GarminSyncRequest(BaseModel):
    email: str
    password: str

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/sync-garmin-activities/")
async def sync_garmin_activities(user_data: GarminSyncRequest, db: Session = Depends(get_db)):
    try:
        logger.info("Starting Garmin sync process")
        
        # Garmin Connect 클라이언트 초기화
        client = Garmin(user_data.email, user_data.password)
        
        # 로그인
        logger.info("Attempting to login to Garmin Connect")
        client.login()
        logger.info("Successfully logged in to Garmin Connect")
        
        # 최근 활동 가져오기 (최근 10개)
        logger.info("Fetching recent activities")
        activities = client.get_activities(0, 100)
        
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

