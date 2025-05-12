from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.activity import Activity, ActivityComment, ActivityFeedback, ActivitySplit
from garminconnect import Garmin
import logging

logger = logging.getLogger(__name__)

class ActivityService:
    """
    Activity 관련 비즈니스 로직을 처리하는 서비스 클래스
    
    이 클래스는 활동 데이터의 조회, 생성, 수정, 삭제 등의 기능을 제공합니다.
    Garmin Connect API와 연동하여 활동 데이터를 동기화하고 처리하는 기능도 포함합니다.
    """
    
    def __init__(self, db: Session):
        """
        ActivityService 초기화
        
        Args:
            db (Session): SQLAlchemy 데이터베이스 세션
        """
        self.db = db

    def get_activities(self, user_id: int):
        """
        특정 사용자의 모든 활동 목록을 조회합니다.
        
        Args:
            user_id (int): 사용자 ID
            
        Returns:
            list: 활동 정보 목록. 각 활동은 다음 정보를 포함:
                - id: 활동의 고유 ID
                - activity_id: Garmin 활동 ID
                - user_id: 사용자 ID
                - activity_name: 활동 이름
                - start_time_local: 현지 시작 시간
                - distance: 거리 (미터)
                - duration: 소요 시간 (초)
                - average_speed: 평균 속도 (m/s)
                - average_hr: 평균 심박수
                - 기타 활동 관련 메트릭
        """
        activities = self.db.query(Activity).filter(Activity.user_id == user_id).all()
        return [{
            "id": activity.id,
            "activity_id": activity.activity_id,
            "user_id": activity.user_id,
            "activity_name": activity.activity_name,
            "start_time_local": activity.start_time_local,
            "start_time_gmt": activity.start_time_gmt,
            "end_time_gmt": activity.end_time_gmt,
            "activity_type": activity.activity_type,
            "event_type": activity.event_type,
            "distance": activity.distance,
            "duration": activity.duration,
            "elapsed_duration": activity.elapsed_duration,
            "moving_duration": activity.moving_duration,
            "elevation_gain": activity.elevation_gain,
            "elevation_loss": activity.elevation_loss,
            "min_elevation": activity.min_elevation,
            "max_elevation": activity.max_elevation,
            "elevation_corrected": activity.elevation_corrected,
            "average_speed": activity.average_speed,
            "max_speed": activity.max_speed,
            "start_latitude": activity.start_latitude,
            "start_longitude": activity.start_longitude,
            "end_latitude": activity.end_latitude,
            "end_longitude": activity.end_longitude,
            "average_hr": activity.average_hr,
            "max_hr": activity.max_hr,
            "hr_time_in_zones": activity.hr_time_in_zones,
            "avg_power": activity.avg_power,
            "max_power": activity.max_power,
            "power_time_in_zones": activity.power_time_in_zones,
            "aerobic_training_effect": activity.aerobic_training_effect,
            "anaerobic_training_effect": activity.anaerobic_training_effect,
            "training_effect_label": activity.training_effect_label,
            "vo2max_value": activity.vo2max_value,
            "average_cadence": activity.average_cadence,
            "max_cadence": activity.max_cadence,
            "avg_vertical_oscillation": activity.avg_vertical_oscillation,
            "avg_ground_contact_time": activity.avg_ground_contact_time,
            "avg_stride_length": activity.avg_stride_length,
            "calories": activity.calories,
            "water_estimated": activity.water_estimated,
            "activity_training_load": activity.activity_training_load,
            "moderate_intensity_minutes": activity.moderate_intensity_minutes,
            "vigorous_intensity_minutes": activity.vigorous_intensity_minutes,
            "steps": activity.steps,
            "time_zone_id": activity.time_zone_id,
            "sport_type_id": activity.sport_type_id,
            "device_id": activity.device_id,
            "manufacturer": activity.manufacturer,
            "lap_count": activity.lap_count,
            "privacy": activity.privacy,
            "favorite": activity.favorite,
            "manual_activity": activity.manual_activity
        } for activity in activities]

    def get_activity(self, activity_id: int):
        """
        특정 활동의 상세 정보를 조회합니다.
        
        Args:
            activity_id (int): 활동 ID
            
        Returns:
            dict: 활동의 상세 정보
            
        Raises:
            HTTPException: 활동을 찾을 수 없는 경우 404 에러
        """
        activity = self.db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        return {
            "id": activity.id,
            "activity_id": activity.activity_id,
            "user_id": activity.user_id,
            "activity_name": activity.activity_name,
            "start_time_local": activity.start_time_local,
            "start_time_gmt": activity.start_time_gmt,
            "end_time_gmt": activity.end_time_gmt,
            "activity_type": activity.activity_type,
            "event_type": activity.event_type,
            "distance": activity.distance,
            "duration": activity.duration,
            "elapsed_duration": activity.elapsed_duration,
            "moving_duration": activity.moving_duration,
            "elevation_gain": activity.elevation_gain,
            "elevation_loss": activity.elevation_loss,
            "min_elevation": activity.min_elevation,
            "max_elevation": activity.max_elevation,
            "elevation_corrected": activity.elevation_corrected,
            "average_speed": activity.average_speed,
            "max_speed": activity.max_speed,
            "start_latitude": activity.start_latitude,
            "start_longitude": activity.start_longitude,
            "end_latitude": activity.end_latitude,
            "end_longitude": activity.end_longitude,
            "average_hr": activity.average_hr,
            "max_hr": activity.max_hr,
            "hr_time_in_zones": activity.hr_time_in_zones,
            "avg_power": activity.avg_power,
            "max_power": activity.max_power,
            "power_time_in_zones": activity.power_time_in_zones,
            "aerobic_training_effect": activity.aerobic_training_effect,
            "anaerobic_training_effect": activity.anaerobic_training_effect,
            "training_effect_label": activity.training_effect_label,
            "vo2max_value": activity.vo2max_value,
            "average_cadence": activity.average_cadence,
            "max_cadence": activity.max_cadence,
            "avg_vertical_oscillation": activity.avg_vertical_oscillation,
            "avg_ground_contact_time": activity.avg_ground_contact_time,
            "avg_stride_length": activity.avg_stride_length,
            "calories": activity.calories,
            "water_estimated": activity.water_estimated,
            "activity_training_load": activity.activity_training_load,
            "moderate_intensity_minutes": activity.moderate_intensity_minutes,
            "vigorous_intensity_minutes": activity.vigorous_intensity_minutes,
            "steps": activity.steps,
            "time_zone_id": activity.time_zone_id,
            "sport_type_id": activity.sport_type_id,
            "device_id": activity.device_id,
            "manufacturer": activity.manufacturer,
            "lap_count": activity.lap_count,
            "privacy": activity.privacy,
            "favorite": activity.favorite,
            "manual_activity": activity.manual_activity
        }
    
    def create_activity(self, user_id: int, activity_data: dict):
        """
        새로운 활동을 생성합니다.
        
        Args:
            activity_data (dict): 활동 데이터
            
        Returns:
            dict: 생성된 활동 정보
        """
        activity = Activity(**activity_data)
        activity.user_id = user_id
        self.db.add(activity)
        self.db.commit()
        return activity

    def get_activities_laps_with_comments(self, user_id: int):
        """
        사용자의 모든 활동과 각 활동의 랩 데이터, 댓글을 조회합니다.
        
        Args:
            user_id (int): 사용자 ID
            
        Returns:
            list: 활동 목록. 각 활동은 다음 정보를 포함:
                - 기본 활동 정보
                - 랩 데이터 (거리, 시간, 페이스, 심박수 등)
                - 댓글 목록
        """
        activities = self.db.query(Activity).filter(Activity.user_id == user_id).order_by(Activity.start_time_local.desc()).all()
        response = []

        for activity in activities:
            laps = self.db.query(ActivitySplit).filter(ActivitySplit.activity_id == activity.activity_id).all()
            comments = self.db.query(ActivityComment).filter(ActivityComment.activity_id == activity.activity_id).all()
            feedback = self.db.query(ActivityFeedback).filter(ActivityFeedback.activity_id == activity.activity_id).first()
            laps_data = []
            comments_data = []
            
            # 랩 데이터 처리
            for lap in laps:
                speed_kmh = lap.average_speed * 3.6
                max_speed_kmh = lap.max_speed * 3.6
                laps_data.append({
                    "lap_index": lap.lap_index,
                    "distance": round(lap.distance / 1000, 2),  # m -> km
                    "duration": self._format_duration(lap.duration),
                    "average_speed": round(speed_kmh, 2),
                    "max_speed": round(max_speed_kmh, 2),
                    "average_pace": self._speed_to_pace(speed_kmh),
                    "max_pace": self._speed_to_pace(max_speed_kmh),
                    "average_hr": lap.average_hr,
                    "max_hr": lap.max_hr,
                    "average_run_cadence": lap.average_run_cadence
                })
            
            # 댓글 데이터 처리
            for comment in comments:
                comments_data.append({
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_at": comment.created_at
                })
            
            # 활동 데이터 변환
            speed_kmh = activity.average_speed * 3.6
            max_speed_kmh = activity.max_speed * 3.6
            response.append({
                "id": activity.id,
                "activity_id": activity.activity_id,
                "activity_name": activity.activity_name,
                "local_start_time": activity.start_time_local,
                "distance": round(activity.distance / 1000, 2),  # m -> km
                "duration": self._format_duration(activity.duration),
                "average_speed": round(speed_kmh, 2),
                "max_speed": round(max_speed_kmh, 2),
                "average_pace": self._speed_to_pace(speed_kmh),
                "max_pace": self._speed_to_pace(max_speed_kmh),
                "average_cadence": activity.average_cadence,
                "average_hr": activity.average_hr,
                "max_hr": activity.max_hr,
                "laps": laps_data,
                "comments": comments_data,
                "feedback": feedback.feedback_data if feedback else None
            })

        return response

    def get_activity_summary(self, user_id: int):
        """
        사용자의 활동 통계 요약 정보를 조회합니다.
        
        Args:
            user_id (int): 사용자 ID
            
        Returns:
            dict: 활동 통계 정보
                - total_activities: 총 활동 수
                - total_distance: 총 거리 (km)
                - total_duration: 총 소요 시간
                - average_pace: 평균 페이스
        """
        activities = self.db.query(Activity).filter(Activity.user_id == user_id).all()
        
        total_activities = len(activities)
        total_distance = sum(activity.distance for activity in activities) / 1000  # m -> km
        total_duration = sum(activity.duration for activity in activities)
        
        # 평균 페이스 계산
        if total_distance > 0:
            avg_speed = (total_distance * 1000) / total_duration  # m/s
            avg_speed_kmh = avg_speed * 3.6  # km/h
            avg_pace = self._speed_to_pace(avg_speed_kmh)
        else:
            avg_pace = "00:00"

        return {
            "total_activities": total_activities,
            "total_distance": round(total_distance, 2),
            "total_duration": self._format_duration(total_duration),
            "average_pace": avg_pace
        }
    
    def get_monthly_activity_summary(self, user_id: int):
        """
        사용자의 월별 활동 통계 정보를 조회합니다.
        
        Args:
            user_id (int): 사용자 ID
            
        Returns:
            dict: 월별 활동 통계 정보
                - month: 월
                - total_distance: 총 거리 (km)
                - total_duration: 총 소요 시간
                - average_pace: 평균 페이스
        """
        activities = self.db.query(Activity).filter(
            Activity.user_id == user_id
        ).all()
        
        monthly_summary = {}
        for activity in activities:
            month = activity.start_time_local.strftime('%Y-%m')
            if month not in monthly_summary:
                monthly_summary[month] = {
                    "total_distance": 0,
                    "total_duration": 0,
                    "average_pace": "00:00"
                }
            monthly_summary[month]["total_distance"] += activity.distance / 1000  # m -> km
            monthly_summary[month]["total_duration"] += activity.duration
        
        for month, data in monthly_summary.items():
            if data["total_duration"] > 0:
                avg_speed = (data["total_distance"] * 1000) / data["total_duration"]  # m/s
                avg_speed_kmh = avg_speed * 3.6  # km/h
                data["average_pace"] = self._speed_to_pace(avg_speed_kmh)

            data["total_duration"] = self._format_duration(data["total_duration"])
        
        return monthly_summary
                

    def create_activity_comment(self, comment_data: dict):
        """
        활동에 새로운 댓글을 추가합니다.
        
        Args:
            comment_data (dict): 댓글 데이터
                - activity_id: 활동 ID
                - comment: 댓글 내용
                
        Returns:
            dict: 성공 메시지
        """
        comment = ActivityComment(
            activity_id=comment_data.get('activity_id'),
            comment=comment_data.get('comment'),
            created_at=datetime.now()
        )
        self.db.add(comment)
        self.db.commit()
        return {"message": "Comment created successfully"}

    def delete_activity_comment(self, comment_id: int):
        """
        활동의 댓글을 삭제합니다.
        
        Args:
            comment_id (int): 삭제할 댓글 ID
            
        Returns:
            dict: 성공 메시지
            
        Raises:
            HTTPException: 댓글을 찾을 수 없는 경우 404 에러
        """
        comment = self.db.query(ActivityComment).filter(ActivityComment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        self.db.delete(comment)
        self.db.commit()
        return {"message": "Comment deleted successfully"}

    def process_activity_splits(self, client: Garmin, activity_id: str):
        """
        Garmin Connect API를 통해 활동의 랩 데이터를 가져와 처리합니다.
        
        Args:
            client (Garmin): Garmin Connect API 클라이언트
            activity_id (str): Garmin 활동 ID
            
        Raises:
            Exception: 랩 데이터 처리 중 오류 발생 시
        """
        try:
            splits_data = client.get_activity_splits(activity_id)
            logger.info(f"Fetched splits data for activity {activity_id}")
            
            if not splits_data or 'lapDTOs' not in splits_data:
                logger.warning(f"No lap data found for activity {activity_id}")
                return

            for lap in splits_data['lapDTOs']:
                try:
                    split = ActivitySplit(
                        activity_id=activity_id,
                        lap_index=lap.get('lapIndex'),
                        start_time_gmt=self._parse_garmin_datetime(lap.get('startTimeGMT')),
                        distance=lap.get('distance'),
                        duration=lap.get('duration'),
                        moving_duration=lap.get('movingDuration'),
                        average_speed=lap.get('averageSpeed'),
                        max_speed=lap.get('maxSpeed'),
                        average_hr=lap.get('averageHR'),
                        max_hr=lap.get('maxHR'),
                        average_run_cadence=lap.get('averageRunCadence'),
                        max_run_cadence=lap.get('maxRunCadence'),
                        average_power=lap.get('averagePower'),
                        max_power=lap.get('maxPower'),
                        ground_contact_time=lap.get('groundContactTime'),
                        stride_length=lap.get('strideLength'),
                        vertical_oscillation=lap.get('verticalOscillation'),
                        vertical_ratio=lap.get('verticalRatio'),
                        calories=lap.get('calories'),
                        elevation_gain=lap.get('elevationGain'),
                        elevation_loss=lap.get('elevationLoss'),
                        max_elevation=lap.get('maxElevation'),
                        min_elevation=lap.get('minElevation'),
                        start_latitude=lap.get('startLatitude'),
                        start_longitude=lap.get('startLongitude'),
                        end_latitude=lap.get('endLatitude'),
                        end_longitude=lap.get('endLongitude')
                    )
                    self.db.add(split)
                    self.db.commit()
                    logger.info(f"Successfully added split {lap.get('lapIndex')} for activity {activity_id}")
                except Exception as e:
                    logger.error(f"Error processing lap data: {str(e)}")
                    self.db.rollback()
                    continue
        except Exception as e:
            logger.error(f"Error fetching splits data: {str(e)}")
            raise

    def save_activity_feedback(self, feedback_data: dict):
        """
        활동에 대한 피드백을 저장합니다.
        
        Args:
            activity_id (int): 활동 ID
            feedback (str): 피드백 내용
            
        Returns:
            dict: 성공 메시지
        """
        feedback = ActivityFeedback(
            user_id=feedback_data.get('user_id'),
            activity_id=feedback_data.get('activity_id'),
            feedback_data=feedback_data.get('feedback_data'),
            created_at=datetime.now()
        )
        self.db.add(feedback)
        self.db.commit()
        return {"message": "Activity feedback saved successfully"}
    
    def get_activity_feedback(self, activity_id: int):
        """
        활동에 대한 피드백을 조회합니다.
        
        Args:
            activity_id (int): 활동 ID
            
        Returns:
            dict: 피드백 정보
        """
        feedback = self.db.query(ActivityFeedback).filter(ActivityFeedback.activity_id == activity_id).first()
        return feedback
    
    def get_activity_laps(self, activity_id: int):
        """
        활동의 랩 데이터를 조회합니다.
        
        Args:
            activity_id (int): 활동 ID
        """
        laps = self.db.query(ActivitySplit).filter(ActivitySplit.activity_id == activity_id).all()
        return [{
            "lap_index": lap.lap_index,
            "distance": lap.distance,
            "duration": lap.duration,
            "average_speed": self._format_pace(lap.average_speed),
            "average_hr": lap.average_hr,
            "max_hr": lap.max_hr,
            "average_run_cadence": lap.average_run_cadence,
        } for lap in laps]

    def _format_duration(self, seconds: float) -> str:
        """
        초 단위 시간을 HH:MM:SS.mmm 형식의 문자열로 변환합니다.
        
        Args:
            seconds (float): 변환할 시간(초)
            
        Returns:
            str: "HH:MM:SS.mmm" 형식의 문자열
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds_remainder):02d}.{milliseconds:03d}"

    def _format_pace(self, seconds_per_km: float) -> str:
        """
        초/km 단위의 페이스를 분:초.mmm/km 형식의 문자열로 변환합니다.
        
        Args:
            seconds_per_km (float): 1km당 소요 시간(초)
            
        Returns:
            str: "분:초.mmm/km" 형식의 문자열
        """
        minutes = int(seconds_per_km // 60)
        seconds_remainder = seconds_per_km % 60
        seconds = int(seconds_remainder)
        milliseconds = int((seconds_remainder - seconds) * 1000)
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

    def _speed_to_pace(self, speed_kmh: float) -> str:
        """
        속도(km/h)를 페이스(분:초.mmm/km)로 변환합니다.
        
        Args:
            speed_kmh (float): 시간당 킬로미터(km/h)
            
        Returns:
            str: "분:초.mmm/km" 형식의 문자열
        """
        if speed_kmh <= 0:
            return "0:00.000"
        seconds_per_km = 3600 / speed_kmh  # 3600초(1시간) / 속도
        return self._format_pace(seconds_per_km)

    def _parse_garmin_datetime(self, date_str: str) -> datetime:
        """
        Garmin에서 제공하는 날짜 문자열을 datetime 객체로 변환합니다.
        
        Args:
            date_str (str): Garmin 날짜 문자열 (예: '2025-05-07T22:20:30.0')
            
        Returns:
            datetime: 변환된 datetime 객체
            
        Raises:
            ValueError: 날짜 문자열 파싱 실패 시
        """
        try:
            if date_str.endswith('.0'):
                date_str = date_str[:-2]
            return datetime.fromisoformat(date_str)
        except ValueError as e:
            logger.error(f"Error parsing date {date_str}: {str(e)}")
            raise 