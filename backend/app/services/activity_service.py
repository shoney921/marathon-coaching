from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.activity import Activity, ActivityComment, ActivitySplit
from garminconnect import Garmin
import logging

logger = logging.getLogger(__name__)

class ActivityService:
    def __init__(self, db: Session):
        self.db = db

    def get_activities(self, user_id: int):
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

    def get_activities_laps_with_comments(self, user_id: int):
        activities = self.db.query(Activity).filter(Activity.user_id == user_id).order_by(Activity.start_time_local.desc()).all()
        response = []

        for activity in activities:
            laps = self.db.query(ActivitySplit).filter(ActivitySplit.activity_id == activity.activity_id).all()
            comments = self.db.query(ActivityComment).filter(ActivityComment.activity_id == activity.activity_id).all()
            laps_data = []
            comments_data = []
            
            for lap in laps:
                speed_kmh = lap.average_speed * 3.6
                max_speed_kmh = lap.max_speed * 3.6
                laps_data.append({
                    "lap_index": lap.lap_index,
                    "distance": round(lap.distance / 1000, 2),
                    "duration": self._format_duration(lap.duration),
                    "average_speed": round(speed_kmh, 2),
                    "max_speed": round(max_speed_kmh, 2),
                    "average_pace": self._speed_to_pace(speed_kmh),
                    "max_pace": self._speed_to_pace(max_speed_kmh),
                    "average_hr": lap.average_hr,
                    "max_hr": lap.max_hr,
                    "average_run_cadence": lap.average_run_cadence
                })
            
            for comment in comments:
                comments_data.append({
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_at": comment.created_at
                })
            
            speed_kmh = activity.average_speed * 3.6
            max_speed_kmh = activity.max_speed * 3.6
            response.append({
                "id": activity.id,
                "activity_id": activity.activity_id,
                "activity_name": activity.activity_name,
                "local_start_time": activity.start_time_local,
                "distance": round(activity.distance / 1000, 2),
                "duration": self._format_duration(activity.duration),
                "average_speed": round(speed_kmh, 2),
                "max_speed": round(max_speed_kmh, 2),
                "average_pace": self._speed_to_pace(speed_kmh),
                "max_pace": self._speed_to_pace(max_speed_kmh),
                "average_cadence": activity.average_cadence,
                "average_hr": activity.average_hr,
                "max_hr": activity.max_hr,
                "laps": laps_data,
                "comments": comments_data
            })

        return response

    def get_activity_summary(self, user_id: int):
        activities = self.db.query(Activity).filter(Activity.user_id == user_id).all()
        
        total_activities = len(activities)
        total_distance = sum(activity.distance for activity in activities) / 1000
        total_duration = sum(activity.duration for activity in activities)
        
        if total_distance > 0:
            avg_speed = (total_distance * 1000) / total_duration
            avg_speed_kmh = avg_speed * 3.6
            avg_pace = self._speed_to_pace(avg_speed_kmh)
        else:
            avg_pace = "00:00"

        return {
            "total_activities": total_activities,
            "total_distance": round(total_distance, 2),
            "total_duration": self._format_duration(total_duration),
            "average_pace": avg_pace
        }

    def create_activity_comment(self, comment_data: dict):
        comment = ActivityComment(
            activity_id=comment_data.get('activity_id'),
            comment=comment_data.get('comment'),
            created_at=datetime.now()
        )
        self.db.add(comment)
        self.db.commit()
        return {"message": "Comment created successfully"}

    def delete_activity_comment(self, comment_id: int):
        comment = self.db.query(ActivityComment).filter(ActivityComment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        self.db.delete(comment)
        self.db.commit()
        return {"message": "Comment deleted successfully"}

    def process_activity_splits(self, client: Garmin, activity_id: str):
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

    def _format_duration(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds_remainder):02d}.{milliseconds:03d}"

    def _format_pace(self, seconds_per_km: float) -> str:
        minutes = int(seconds_per_km // 60)
        seconds_remainder = seconds_per_km % 60
        seconds = int(seconds_remainder)
        milliseconds = int((seconds_remainder - seconds) * 1000)
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

    def _speed_to_pace(self, speed_kmh: float) -> str:
        if speed_kmh <= 0:
            return "0:00.000"
        seconds_per_km = 3600 / speed_kmh
        return self._format_pace(seconds_per_km)

    def _parse_garmin_datetime(self, date_str: str) -> datetime:
        try:
            if date_str.endswith('.0'):
                date_str = date_str[:-2]
            return datetime.fromisoformat(date_str)
        except ValueError as e:
            logger.error(f"Error parsing date {date_str}: {str(e)}")
            raise 