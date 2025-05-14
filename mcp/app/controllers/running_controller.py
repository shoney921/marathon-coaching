from typing import Dict, Any
from ..protocols.mcp_protocol import MCPRequest, MCPResponse, MCPError
from ..providers.backend_provider import BackendProvider
from ..providers.ai_provider import AIProvider
import logging
from fastapi import Request, HTTPException

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
            elif request.action == "create_training_schedule":
                return await self._handle_create_training_schedule(request)
            elif request.action == "running_coach_prompt":
                return await self._handle_running_coach_prompt(request)
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
            laps = request.parameters.get("laps")
            
            if not user_id or not query:
                raise MCPError("user_id and query are required", "MISSING_PARAMETER")
            
            analysis = await self.ai_provider.analyze_activity(user_id, query, comments, laps)
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

    async def _handle_create_training_schedule(self, request: MCPRequest) -> MCPResponse:
        try:
            user_id = request.parameters.get("user_id")
            race_name = request.parameters.get("race_name")
            race_date = request.parameters.get("race_date")
            race_type = request.parameters.get("race_type")
            race_time = request.parameters.get("race_time")
            special_notes = request.parameters.get("special_notes")
            
            if not user_id or not race_name or not race_date or not race_type or not race_time:
                raise MCPError("All parameters are required", "MISSING_PARAMETER")
            
            training_schedule = await self.ai_provider.create_training_schedule(
                user_id=user_id,
                race_name=race_name,
                race_date=race_date,
                race_type=race_type,
                race_time=race_time,
                special_notes=special_notes
            )
            return MCPResponse(
                status="success",
                data={"training_schedule": training_schedule}
            )
        except Exception as e:
            logger.error(f"Race training creation failed: {str(e)}")
            return MCPResponse(
                status="error",
                error=str(e),
                data=None
            ) 
        
    async def _handle_running_coach_prompt(self, request: MCPRequest) -> MCPResponse:
        try:
            user_id = request.parameters.get("user_id")
            user_message = request.parameters.get("user_message") or request.parameters.get("query")
            chat_history = request.parameters.get("chat_history")
            logger.info(f"## user_id: {user_id}")
            logger.info(f"## user_message: {user_message}")
            logger.info(f"## chat_history: {chat_history}")
            if not user_id or not user_message:
                raise MCPError("user_id and user_message/query are required", "MISSING_PARAMETER")
            
            response = await self.ai_provider.running_coach_prompt(
                user_id=user_id,
                user_message=user_message,
                chat_history=chat_history
            )
            return MCPResponse(
                status="success",
                data={"response": response}
            )
        except Exception as e:
            logger.error(f"Running coach prompt generation failed: {str(e)}")
            