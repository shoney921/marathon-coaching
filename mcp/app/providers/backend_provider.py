import os
import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BackendProvider:
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:8001")
        if not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f"http://{self.base_url}"

    async def get_running_activities(self, user_id: int) -> Dict[str, Any]:
        """러닝 활동 데이터를 조회합니다."""
        url = f"{self.base_url}/activities/laps/user/{user_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API 호출 실패: {error_text}")
                        raise Exception(f"API 호출 실패: {error_text}")
        except Exception as e:
            logger.error(f"러닝 활동 조회 실패: {str(e)}")
            raise

    async def get_monthly_activity_summary(self, user_id: int) -> Dict[str, Any]:
        """월간 활동 요약을 조회합니다."""
        url = f"{self.base_url}/activities/monthly-summary/user/{user_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API 호출 실패: {error_text}")
                        raise Exception(f"API 호출 실패: {error_text}")
        except Exception as e:
            logger.error(f"월간 요약 조회 실패: {str(e)}")
            raise 