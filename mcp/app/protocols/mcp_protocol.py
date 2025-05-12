from typing import Dict, Any, Optional
from pydantic import BaseModel

class MCPRequest(BaseModel):
    """MCP 요청 프로토콜"""
    action: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    """MCP 응답 프로토콜"""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MCPError(Exception):
    """MCP 프로토콜 에러"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message) 