from typing import Dict, Any
from ..protocols.mcp_protocol import MCPRequest, MCPResponse, MCPError
from ..providers.backend_provider import BackendProvider
from ..providers.ai_provider import AIProvider
import logging

logger = logging.getLogger(__name__)

class RunningController:
    def __init__(self):
        self.backend_provider = BackendProvider()
        self.ai_provider = AIProvider()

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """MCP 요청을 처리하는 메인 컨트롤러 메서드"""
        try:
            if request.action == "get_running_activities":
                return await self._handle_get_activities(request)
            elif request.action == "get_monthly_summary":
                return await self._handle_get_monthly_summary(request)
            elif request.action == "analyze_activity":
                return await self._handle_analyze_activity(request)
            else:
                raise MCPError(f"Unknown action: {request.action}", "INVALID_ACTION")
        except MCPError as e:
            return MCPResponse(status="error", error=e.message)
        except Exception as e:
            return MCPResponse(status="error", error=str(e))

    async def _handle_get_activities(self, request: MCPRequest) -> MCPResponse:
        user_id = request.parameters.get("user_id")
        if not user_id:
            raise MCPError("user_id is required", "MISSING_PARAMETER")
        
        activities = await self.backend_provider.get_running_activities(user_id)
        return MCPResponse(
            status="success",
            data={"activities": activities}
        )

    async def _handle_get_monthly_summary(self, request: MCPRequest) -> MCPResponse:
        user_id = request.parameters.get("user_id")
        if not user_id:
            raise MCPError("user_id is required", "MISSING_PARAMETER")
        
        summary = await self.backend_provider.get_monthly_activity_summary(user_id)
        return MCPResponse(
            status="success",
            data={"summary": summary}
        )

    async def _handle_analyze_activity(self, request: MCPRequest) -> MCPResponse:
        try:
            user_id = request.parameters.get("user_id")
            query = request.parameters.get("query")
            comments = request.parameters.get("comments")
            
            if not user_id or not query:
                raise MCPError("user_id and query are required", "MISSING_PARAMETER")
            
            analysis = await self.ai_provider.analyze_activity(user_id, query, comments)
            return MCPResponse(
                status="success",
                data={"analysis": analysis}
            )
        except Exception as e:
            logger.error(f"Activity analysis failed: {str(e)}")
            return MCPResponse(
                status="error",
                error=str(e),
                data=None
            ) 