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

    def create_tools(self, user_id: int, tool_names: List[str] = None) -> List[Tool]:
        """요청된 도구들을 생성하여 반환"""
        logger.info("도구 생성 시작")
        
        # 도구 생성 함수 매핑
        tool_creators = {
            "GetRunningActivities": lambda: self.create_get_activities_tool(user_id),
            "GetMonthlyActivitySummary": lambda: self.create_get_monthly_summary_tool(user_id)
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