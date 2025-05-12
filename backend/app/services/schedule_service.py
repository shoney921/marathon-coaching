from datetime import datetime
from typing import Dict, Any
import logging
import aiohttp
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ScheduleService:
    def __init__(self, db: Session):
        self.db = db
        self.mcp_url = "http://localhost:8000"  # MCP 서버 URL 설정 필요

    async def create_race_training_schedule(
        self,
        user_id: int,
        race_name: str,
        race_date: str,
        race_type: str,
        race_time: str
    ) -> Dict[str, Any]:
        """
        MCP 서버에 훈련 일정 생성 요청
        
        Args:
            user_id: 사용자 ID
            race_name: 대회명
            race_date: 대회 날짜
            race_type: 대회 종류
            race_time: 목표 시간
            
        Returns:
            훈련 일정 데이터
        """
        try:
            # MCP 서버에 요청할 데이터 준비
            request_data = {
                "action": "create_race_training",
                "parameters": {
                    "user_id": user_id,
                    "race_name": race_name,
                    "race_date": race_date,
                    "race_type": race_type,
                    "race_time": race_time
                }
            }

            # MCP 서버에 요청
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_url}/mcp",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        schedule_data = await response.json()
                        logger.info(f"훈련 일정 생성 성공: {schedule_data}")
                        return schedule_data.get("data", {}).get("training_schedule", {})
                    else:
                        error_msg = await response.text()
                        logger.error(f"훈련 일정 생성 실패: {error_msg}")
                        raise Exception(f"MCP 서버 오류: {error_msg}")

        except Exception as e:
            logger.error(f"훈련 일정 생성 중 오류 발생: {str(e)}")
            raise

    def save_training_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        생성된 훈련 일정 저장
        
        Args:
            schedule_data: 훈련 일정 데이터
            
        Returns:
            저장된 훈련 일정
        """
        try:
            # TODO: DB에 훈련 일정 저장 로직 구현
            return schedule_data
        except Exception as e:
            logger.error(f"훈련 일정 저장 실패: {str(e)}")
            raise
