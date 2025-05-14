import os
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BackendProvider:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8001")

    def get_running_activities(self, user_id: int) -> Dict[str, Any]:
        """러닝 활동 데이터를 조회합니다."""
        url = f"{self.base_url}/activities/laps/user/{user_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API 호출 실패: {response.text}")
                raise Exception(f"API 호출 실패: {response.text}")
        except Exception as e:
            logger.error(f"러닝 활동 조회 실패: {str(e)}")
            raise

    def get_monthly_activity_summary(self, user_id: int) -> Dict[str, Any]:
        """월간 활동 요약 데이터를 조회합니다."""
        url = f"{self.base_url}/activities/monthly-summary/user/{user_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API 호출 실패: {response.text}")
                raise Exception(f"API 호출 실패: {response.text}")
        except Exception as e:
            logger.error(f"월간 활동 요약 조회 실패: {str(e)}")
            raise 