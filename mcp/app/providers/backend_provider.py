import os
import logging
import requests
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BackendProvider:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_running_activities(self, user_id: int) -> List[Dict[str, Any]]:
        """러닝 활동 데이터 조회"""
        try:
            response = self.session.get(f"{self.base_url}/activities/laps/user/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"러닝 활동 데이터 조회 실패: {str(e)}")
            return []

    def get_monthly_activity_summary(self, user_id: int) -> Dict[str, Any]:
        """월간 활동 요약 조회"""
        try:
            response = self.session.get(f"{self.base_url}/activities/monthly-summary/user/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"월간 활동 요약 조회 실패: {str(e)}")
            return {}

    def get_schedules(self, user_id: int) -> List[Dict[str, Any]]:
        """훈련 일정 조회"""
        try:
            response = self.session.get(f"{self.base_url}/schedules/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"훈련 일정 조회 실패: {str(e)}")
            return []

    def update_schedule(self, user_id: int, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """훈련 일정 수정"""
        try:
            logger.info(f"일정 수정 요청 데이터: {schedule}")
            
            # 일정 데이터 유효성 검사
            required_fields = ["id", "title", "schedule_datetime", "description", "type"]
            if not all(field in schedule for field in required_fields):
                missing_fields = [field for field in required_fields if field not in schedule]
                raise ValueError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")

            # datetime 형식 검증
            try:
                datetime.fromisoformat(schedule["schedule_datetime"].replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("잘못된 datetime 형식입니다.")

            # type 값 검증
            if schedule["type"] not in ["훈련", "대회"]:
                raise ValueError("type은 '훈련' 또는 '대회'여야 합니다.")

            # API 요청을 위한 데이터 변환
            api_schedule = {
                "id": int(schedule["id"]),  # 문자열 ID를 정수로 변환
                "title": schedule["title"],
                "datetime": schedule["schedule_datetime"],  # API 요구사항에 맞게 필드명 변환
                "description": schedule["description"],
                "type": schedule["type"]
            }
            
            logger.info(f"API 요청 데이터: {api_schedule}")

            response = self.session.put(
                f"{self.base_url}/schedules/{user_id}/{api_schedule['id']}",
                json=api_schedule
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"API 응답 데이터: {result}")
            
            return result
        except Exception as e:
            logger.error(f"훈련 일정 수정 실패: {str(e)}")
            raise
