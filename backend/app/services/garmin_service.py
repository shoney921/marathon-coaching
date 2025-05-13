from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from garminconnect import Garmin
from app.models.activity import Activity
import logging

logger = logging.getLogger(__name__)

class GarminService:
    """
    Garmin Connect API와의 연동을 처리하는 서비스 클래스
    
    이 클래스는 Garmin Connect API를 통해 활동 데이터를 동기화하고,
    가민 활동 데이터를 처리하는 기능을 제공합니다.
    """
    
    def __init__(self, db: Session):
        """
        GarminService 초기화
        
        Args:
            db (Session): SQLAlchemy 데이터베이스 세션
        """
        self.db = db

    def check_garmin_login(self, email: str, password: str):
        """
        Garmin Connect 로그인 여부를 확인합니다.
        
        Args:
            email (str): Garmin Connect 이메일  
            password (str): Garmin Connect 비밀번호
            
        Returns:
            bool: 로그인 여부
        """
        client = Garmin(email, password)
        return client.login()

    def sync_activities(self, user_id: int, garmin_email: str, garmin_password: str):
        """
        Garmin Connect에서 사용자의 활동 데이터를 동기화합니다.
        
        Args:
            user_id (int): 사용자 ID
            email (str): Garmin Connect 이메일
            password (str): Garmin Connect 비밀번호
            
        Returns:
            dict: 동기화 결과 정보
                - message: 성공 메시지
                - total_activities: 동기화된 총 활동 수
                
        Raises:
            HTTPException: Garmin Connect 로그인 실패 또는 활동 데이터 가져오기 실패 시
        """
        try:
            logger.info("Starting Garmin sync process")
            
            # Garmin Connect 클라이언트 초기화
            client = Garmin(garmin_email, garmin_password)
            
            # 로그인
            logger.info("Attempting to login to Garmin Connect")
            try:
                client.login()
                logger.info("Successfully logged in to Garmin Connect")
            except Exception as e:
                logger.error(f"Failed to login to Garmin Connect: {str(e)}")
                raise HTTPException(status_code=401, detail="Failed to login to Garmin Connect")
            
            # 최근 활동 가져오기 (최근 100개)
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
                try:
                    # 이미 저장된 활동인지 확인
                    existing_activity = self.db.query(Activity).filter(
                        Activity.user_id == user_id,
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
                    
                    self.db.add(activity)
                    self.db.flush()  # ID를 얻기 위해 flush
                    
                    synced_count += 1
                    logger.info(f"Successfully added activity {activity_data.get('activityId')}")

                    self.process_activity_splits(client, activity_data.get('activityId'))
                    
                except Exception as e:
                    logger.error(f"Error processing activity {activity_data.get('activityId')}: {str(e)}")
                    continue
            
            self.db.commit()
            logger.info(f"Sync completed. Synced {synced_count} activities")
            return {
                "message": f"Successfully synced {synced_count} activities",
                "total_activities": len(activities)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during sync process: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def process_activity_splits(self, client: Garmin, activity_id: str):
        """
        Garmin Connect API를 통해 활동의 랩 데이터를 가져와 처리합니다.
        
        Args:
            client (Garmin): Garmin Connect API 클라이언트
            activity_id (str): Garmin 활동 ID
            
        Returns:
            dict: 성공 메시지
            
        Raises:
            HTTPException: 활동을 찾을 수 없거나 랩 데이터 처리 중 오류 발생 시
        """
        try:
            # 활동이 존재하는지 확인
            activity = self.db.query(Activity).filter(Activity.activity_id == str(activity_id)).first()
            if not activity:
                raise HTTPException(status_code=404, detail="Activity not found")
            
            logger.info(f"activity {str(activity.activity_id)}")
            
            # ActivityService를 사용하여 랩 데이터 처리
            from app.services.activity_service import ActivityService
            activity_service = ActivityService(self.db)
            activity_service.process_activity_splits(client, str(activity.activity_id))
            return {"message": "Activity splits processed successfully"}
            
        except Exception as e:
            logger.error(f"Error in process_activity_splits: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 