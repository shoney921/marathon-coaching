import logging
import json
from typing import Dict, Any, List
from langchain_core.tools import Tool
from .backend_provider import BackendProvider

logger = logging.getLogger(__name__)

class ToolManager:
    def __init__(self, backend_provider: BackendProvider):
        self.backend_provider = backend_provider

    def create_get_activities_tool(self, user_id: int) -> Tool:
        """러닝 활동 조회 도구 생성"""
        def get_activities(_):
            try:
                logger.info("GetRunningActivities 도구 실행 시작")
                result = self.backend_provider.get_running_activities(user_id)
                logger.info(f"GetRunningActivities 결과: {result}")
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_activities: {str(e)}")
                return "[]"
        
        return Tool(
            name="GetRunningActivities",
            func=get_activities,
            description="모든 러닝 활동 데이터를 조회합니다. 러닝 활동 데이터는 러닝 활동 이름, 시작 시간, 거리, 소요시간, 페이스, 심박수, 칼로리, 위치, 날씨, 노트 등의 정보를 포함합니다."
        )

    def create_get_monthly_summary_tool(self, user_id: int) -> Tool:
        """월간 활동 요약 도구 생성"""
        def get_monthly_summary(_):
            try:
                logger.info("GetMonthlyActivitySummary 도구 실행 시작")
                result = self.backend_provider.get_monthly_activity_summary(user_id)
                logger.info(f"GetMonthlyActivitySummary 결과: {result}")
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_monthly_summary: {str(e)}")
                return "{}"
        
        return Tool(
            name="GetMonthlyActivitySummary",
            func=get_monthly_summary,
            description="러닝 활동 월간 통계를 조회합니다. 월별 거리, 소요시간, 평균 페이스를 조회합니다."
        )

    def create_get_schedules_tool(self, user_id: int) -> Tool:
        """훈련 일정 조회 도구 생성"""
        def get_schedules(_):
            try:
                logger.info("GetSchedules 도구 실행 시작")
                result = self.backend_provider.get_schedules(user_id)
                logger.info(f"GetSchedules 결과: {result}")
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_schedules: {str(e)}")
                return "[]"
        
        return Tool(
            name="GetSchedules",
            func=get_schedules,
            description="사용자의 모든 훈련 일정을 조회합니다. 각 일정은 제목, 날짜, 시간, 설명, 유형 등의 정보를 포함합니다."
        )

    def create_update_schedule_tool(self, user_id: int) -> Tool:
        """훈련 일정 수정 도구 생성"""
        def update_schedule(schedule_data: str):
            try:
                logger.info("UpdateSchedule 도구 실행 시작")
                schedule = json.loads(schedule_data)
                result = self.backend_provider.update_schedule(user_id, schedule)
                logger.info(f"UpdateSchedule 결과: {result}")
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in update_schedule: {str(e)}")
                return "{}"
        
        return Tool(
            name="UpdateSchedule",
            func=update_schedule,
            description="""훈련 일정을 수정합니다. 입력은 다음 형식의 JSON 문자열이어야 합니다:
            {
                "id": "일정 ID",
                "title": "일정 제목",
                "schedule_datetime": "YYYY-MM-DDTHH:mm:ss",
                "description": "일정 설명",
                "type": "훈련/대회"
            }"""
        )

    def create_tools(self, user_id: int, tool_names: List[str] = None) -> List[Tool]:
        """요청된 도구들을 생성하여 반환"""
        logger.info("도구 생성 시작")
        
        # 도구 생성 함수 매핑
        tool_creators = {
            "GetRunningActivities": lambda: self.create_get_activities_tool(user_id),
            "GetMonthlyActivitySummary": lambda: self.create_get_monthly_summary_tool(user_id),
            "GetSchedules": lambda: self.create_get_schedules_tool(user_id),
            "UpdateSchedule": lambda: self.create_update_schedule_tool(user_id)
        }
        
        # 도구 이름이 지정되지 않은 경우 모든 도구 생성
        if tool_names is None:
            tool_names = list(tool_creators.keys())
        
        # 요청된 도구들 생성
        tools = []
        for tool_name in tool_names:
            if tool_name in tool_creators:
                tool = tool_creators[tool_name]()
                tools.append(tool)
            else:
                logger.warning(f"알 수 없는 도구 이름: {tool_name}")
        
        logger.info(f"생성된 도구: {[tool.name for tool in tools]}")
        return tools