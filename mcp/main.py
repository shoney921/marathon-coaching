from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Running Activity MCP Server")

# 백엔드 API 클라이언트
class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_running_activities(self):
        response = requests.get(f"{self.base_url}/api/running-activities")
        return response.json()

    async def get_activity_stats(self):
        response = requests.get(f"{self.base_url}/api/activity-stats")
        return response.json()

# AI 에이전트 설정
class RunningActivityAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [
            Tool(
                name="GetRunningActivities",
                func=self.get_running_activities,
                description="러닝 활동 데이터를 조회합니다."
            ),
            Tool(
                name="GetActivityStats",
                func=self.get_activity_stats,
                description="러닝 활동 통계를 조회합니다."
            )
        ]
        self.agent = self._create_agent()

    def _create_agent(self):
        prompt = StringPromptTemplate.from_template(
            """당신은 러닝 활동 데이터를 분석하는 AI 어시스턴트입니다.
            사용자의 질문에 답변하기 위해 다음 도구들을 사용할 수 있습니다:
            
            {tools}
            
            질문: {input}
            {agent_scratchpad}
            """
        )
        
        return LLMSingleActionAgent(
            llm_chain=self.llm,
            output_parser=self._parse_output,
            stop=["\nObservation:"],
            allowed_tools=[tool.name for tool in self.tools]
        )

    async def process_query(self, query: str):
        try:
            response = await self.agent.arun(query)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# API 엔드포인트
class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def process_query(request: QueryRequest):
    agent = RunningActivityAgent()
    response = await agent.process_query(request.query)
    return {"response": response}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 