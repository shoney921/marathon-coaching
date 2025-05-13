from datetime import datetime
from typing import Dict, Any, List
import logging
import aiohttp
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.schedule import TrainingSchedule

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
        race_time: str,
        special_notes: str
    ) -> List[Dict[str, Any]]:
        """
        MCP 서버에 훈련 일정 생성 요청 및 DB 저장
        
        Args:
            user_id: 사용자 ID
            race_name: 대회명
            race_date: 대회 날짜
            race_type: 대회 종류
            race_time: 목표 시간
            special_notes: 특이사항
        Returns:
            생성된 훈련 일정 목록
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
                    "race_time": race_time,
                    "special_notes": special_notes
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
                        
                        # JSON 문자열에서 실제 데이터 추출
                        training_schedule = schedule_data.get("data", {}).get("training_schedule", {}).get("training_schedule", "")
                        if training_schedule.startswith("```json"):
                            training_schedule = training_schedule.replace("```json", "").replace("```", "").strip()
                        
                        schedule_dict = json.loads(training_schedule)
                        schedules = schedule_dict.get("schedules", [])
                        
                        # DB에 저장
                        saved_schedules = []
                        for schedule in schedules:
                            db_schedule = TrainingSchedule(
                                user_id=user_id,
                                title=schedule["title"],
                                schedule_datetime=datetime.fromisoformat(schedule["datetime"]),
                                description=schedule["description"],
                                type=schedule["type"]
                            )
                            self.db.add(db_schedule)
                            saved_schedules.append(db_schedule)
                        
                        self.db.commit()
                        
                        # 저장된 일정 반환
                        return [schedule.to_dict() for schedule in saved_schedules]
                    else:
                        error_msg = await response.text()
                        logger.error(f"훈련 일정 생성 실패: {error_msg}")
                        raise Exception(f"MCP 서버 오류: {error_msg}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"훈련 일정 생성 중 오류 발생: {str(e)}")
            raise

    def get_user_schedules(
        self,
        user_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        schedule_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        사용자의 훈련 일정 조회
        
        Args:
            user_id: 사용자 ID
            start_date: 시작 날짜 (선택)
            end_date: 종료 날짜 (선택)
            schedule_type: 일정 유형 (선택)
        Returns:
            훈련 일정 목록
        """
        try:
            query = self.db.query(TrainingSchedule).filter(TrainingSchedule.user_id == user_id)
            
            # 날짜 필터링
            if start_date is not None:
                query = query.filter(TrainingSchedule.schedule_datetime >= start_date)
            if end_date is not None:
                query = query.filter(TrainingSchedule.schedule_datetime <= end_date)
            if schedule_type is not None:
                query = query.filter(TrainingSchedule.type == schedule_type)
            
            # 날짜순으로 정렬
            schedules = query.order_by(TrainingSchedule.schedule_datetime).all()
            
            return [schedule.to_dict() for schedule in schedules]
            
        except Exception as e:
            logger.error(f"훈련 일정 조회 중 오류 발생: {str(e)}")
            raise

    def get_schedule_by_id(self, schedule_id: int, user_id: int) -> Dict[str, Any]:
        """
        특정 훈련 일정 조회
        
        Args:
            schedule_id: 일정 ID
            user_id: 사용자 ID
        Returns:
            훈련 일정 정보
        """
        try:
            schedule = self.db.query(TrainingSchedule).filter(
                TrainingSchedule.id == schedule_id,
                TrainingSchedule.user_id == user_id
            ).first()
            
            if not schedule:
                raise Exception("일정을 찾을 수 없습니다.")
                
            return schedule.to_dict()
            
        except Exception as e:
            logger.error(f"훈련 일정 조회 중 오류 발생: {str(e)}")
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

    def delete_schedule(self, schedule_id: int, user_id: int) -> Dict[str, Any]:
        """
        훈련 일정 삭제
        
        Args:
            schedule_id: 일정 ID
            user_id: 사용자 ID
        Returns:
            삭제된 일정 정보
        """
        try:
            schedule = self.db.query(TrainingSchedule).filter(
                TrainingSchedule.id == schedule_id,
                TrainingSchedule.user_id == user_id
            ).first()
            
            if not schedule:
                raise Exception("일정을 찾을 수 없습니다.")
            
            self.db.delete(schedule)
            self.db.commit()
            
            return schedule.to_dict()
        
        except Exception as e:
            logger.error(f"훈련 일정 삭제 중 오류 발생: {str(e)}")
            raise
        
