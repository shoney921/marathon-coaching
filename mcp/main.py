from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
import requests
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import Tool
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
import os
from dotenv import load_dotenv
from google.cloud import aiplatform
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# GCP 인증 설정
try:
    # 서비스 계정 키 파일 경로 확인
    key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "gcp-key.json")
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"GCP 서비스 계정 키 파일을 찾을 수 없습니다: {key_file}")
    
    # Vertex AI 초기화
    aiplatform.init(
        project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )
    logger.info("GCP AI Platform initialized successfully")
except Exception as e:
    logger.error(f"GCP 초기화 실패: {str(e)}")
    logger.error("다음 사항을 확인해주세요:")
    logger.error("1. gcp-key.json 파일이 올바른 위치에 있는지")
    logger.error("2. .env 파일에 GCP_PROJECT_ID와 GCP_LOCATION이 설정되어 있는지")
    logger.error("3. 서비스 계정에 필요한 권한이 부여되어 있는지")
    raise

app = FastAPI(title="Running Activity MCP Server")

# 백엔드 API 클라이언트
class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_running_activities(self):
        try:
            # 테스트 데이터 반환
            return [
                {
                    "id": 1,
                    "activity_id": "run_001",
                    "user_id": 1,
                    "activity_name": "아침 러닝",
                    "start_time_local": "2024-03-20T06:30:00",
                    "distance": 5.2,
                    "duration": 1800,
                    "pace": 5.45,
                    "heart_rate": 145,
                    "calories": 320,
                    "notes": "날씨가 좋아서 페이스가 잘 나왔음",
                    "location": "서울숲공원",
                    "weather": {"temperature": 15, "condition": "맑음"},
                    "splits": [
                        {"km": 1, "pace": 5.30, "heart_rate": 140},
                        {"km": 2, "pace": 5.40, "heart_rate": 145},
                        {"km": 3, "pace": 5.50, "heart_rate": 150},
                        {"km": 4, "pace": 5.45, "heart_rate": 148},
                        {"km": 5, "pace": 5.40, "heart_rate": 145}
                    ]
                },
                {
                    "id": 2,
                    "activity_id": "run_002",
                    "user_id": 1,
                    "activity_name": "저녁 러닝",
                    "start_time_local": "2024-03-21T18:00:00",
                    "distance": 7.5,
                    "duration": 2700,
                    "pace": 6.00,
                    "heart_rate": 155,
                    "calories": 450,
                    "notes": "힘들었지만 완주함",
                    "location": "한강공원",
                    "weather": {"temperature": 18, "condition": "흐림"},
                    "splits": [
                        {"km": 1, "pace": 5.45, "heart_rate": 150},
                        {"km": 2, "pace": 5.55, "heart_rate": 155},
                        {"km": 3, "pace": 6.00, "heart_rate": 160},
                        {"km": 4, "pace": 6.10, "heart_rate": 162},
                        {"km": 5, "pace": 6.15, "heart_rate": 165},
                        {"km": 6, "pace": 6.20, "heart_rate": 168},
                        {"km": 7, "pace": 6.25, "heart_rate": 170}
                    ]
                },
                {
                    "id": 3,
                    "activity_id": "run_003",
                    "user_id": 1,
                    "activity_name": "주말 장거리 러닝",
                    "start_time_local": "2024-03-23T08:00:00",
                    "distance": 15.0,
                    "duration": 5400,
                    "pace": 6.00,
                    "heart_rate": 150,
                    "calories": 900,
                    "notes": "마라톤 대비 장거리 훈련",
                    "location": "북악산 코스",
                    "weather": {"temperature": 12, "condition": "맑음"},
                    "splits": [
                        {"km": 1, "pace": 5.30, "heart_rate": 145},
                        {"km": 2, "pace": 5.40, "heart_rate": 148},
                        {"km": 3, "pace": 5.50, "heart_rate": 150},
                        {"km": 4, "pace": 6.00, "heart_rate": 152},
                        {"km": 5, "pace": 6.10, "heart_rate": 155},
                        {"km": 6, "pace": 6.20, "heart_rate": 158},
                        {"km": 7, "pace": 6.30, "heart_rate": 160},
                        {"km": 8, "pace": 6.40, "heart_rate": 162},
                        {"km": 9, "pace": 6.50, "heart_rate": 165},
                        {"km": 10, "pace": 7.00, "heart_rate": 168},
                        {"km": 11, "pace": 7.10, "heart_rate": 170},
                        {"km": 12, "pace": 7.20, "heart_rate": 172},
                        {"km": 13, "pace": 7.30, "heart_rate": 175},
                        {"km": 14, "pace": 7.40, "heart_rate": 178},
                        {"km": 15, "pace": 7.50, "heart_rate": 180}
                    ]
                },
                {
                    "id": 4,
                    "activity_id": "run_004",
                    "user_id": 1,
                    "activity_name": "인터벌 트레이닝",
                    "start_time_local": "2024-03-24T17:30:00",
                    "distance": 8.0,
                    "duration": 2400,
                    "pace": 5.00,
                    "heart_rate": 165,
                    "calories": 480,
                    "notes": "400m 인터벌 8세트 완료",
                    "location": "운동장",
                    "weather": {"temperature": 16, "condition": "맑음"},
                    "splits": [
                        {"km": 0.4, "pace": 4.30, "heart_rate": 170},
                        {"km": 0.2, "pace": 6.00, "heart_rate": 160},
                        {"km": 0.4, "pace": 4.30, "heart_rate": 175},
                        {"km": 0.2, "pace": 6.00, "heart_rate": 165},
                        {"km": 0.4, "pace": 4.30, "heart_rate": 180},
                        {"km": 0.2, "pace": 6.00, "heart_rate": 170},
                        {"km": 0.4, "pace": 4.30, "heart_rate": 185},
                        {"km": 0.2, "pace": 6.00, "heart_rate": 175}
                    ]
                }
            ]
        except Exception as e:
            logger.error(f"Failed to fetch running activities: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch running activities")

    async def get_activity_stats(self):
        try:
            # 테스트 데이터 반환
            return {
                "total_distance": 35.7,
                "total_duration": 12300,
                "average_pace": 5.75,
                "total_calories": 2150,
                "weekly_stats": {
                    "distance": 35.7,
                    "duration": 12300,
                    "activities": 4,
                    "average_heart_rate": 153,
                    "pace_distribution": {
                        "easy": 1,
                        "moderate": 2,
                        "hard": 1
                    }
                },
                "monthly_stats": {
                    "distance": 120.5,
                    "duration": 43200,
                    "activities": 15,
                    "average_heart_rate": 151,
                    "pace_distribution": {
                        "easy": 5,
                        "moderate": 7,
                        "hard": 3
                    }
                },
                "pace_distribution": {
                    "easy": 1,
                    "moderate": 2,
                    "hard": 1
                },
                "heart_rate_zones": {
                    "zone1": 1800,  # 120-130 bpm
                    "zone2": 3600,  # 130-140 bpm
                    "zone3": 4200,  # 140-150 bpm
                    "zone4": 1800,  # 150-160 bpm
                    "zone5": 900    # 160+ bpm
                },
                "training_load": {
                    "acute": 85,
                    "chronic": 75,
                    "fitness": 80,
                    "fatigue": 65
                },
                "improvement_metrics": {
                    "pace_improvement": -0.5,  # 분/km 단위로 개선
                    "distance_increase": 2.5,  # km 단위로 증가
                    "endurance_increase": 15   # % 단위로 증가
                },
                "achievements": [
                    {
                        "name": "주간 거리 목표 달성",
                        "description": "주간 30km 목표 달성",
                        "date": "2024-03-24"
                    },
                    {
                        "name": "인터벌 트레이닝 완료",
                        "description": "400m 인터벌 8세트 완료",
                        "date": "2024-03-24"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Failed to fetch activity stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch activity stats")

# AI 에이전트 설정
class RunningActivityAgent:
    def __init__(self):
        try:
            self.llm = ChatVertexAI(
                model_name="gemini-pro",
                temperature=0,
                max_output_tokens=1024,
                top_p=0.8,
                top_k=40,
                location=os.getenv("GCP_LOCATION", "us-central1"),
                project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai")
            )
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
            logger.info("RunningActivityAgent initialized successfully with Gemini Pro")
        except Exception as e:
            logger.error(f"Failed to initialize RunningActivityAgent: {str(e)}")
            raise

    def get_running_activities(self):
        # 테스트 데이터 반환
        return [
            {
                "id": 1,
                "activity_id": "run_001",
                "user_id": 1,
                "activity_name": "아침 러닝",
                "start_time_local": "2024-03-20T06:30:00",
                "distance": 5.2,
                "duration": 1800,
                "pace": 5.45,
                "heart_rate": 145,
                "calories": 320,
                "notes": "날씨가 좋아서 페이스가 잘 나왔음",
                "location": "서울숲공원",
                "weather": {"temperature": 15, "condition": "맑음"},
                "splits": [
                    {"km": 1, "pace": 5.30, "heart_rate": 140},
                    {"km": 2, "pace": 5.40, "heart_rate": 145},
                    {"km": 3, "pace": 5.50, "heart_rate": 150},
                    {"km": 4, "pace": 5.45, "heart_rate": 148},
                    {"km": 5, "pace": 5.40, "heart_rate": 145}
                ]
            },
            {
                "id": 2,
                "activity_id": "run_002",
                "user_id": 1,
                "activity_name": "저녁 러닝",
                "start_time_local": "2024-03-21T18:00:00",
                "distance": 7.5,
                "duration": 2700,
                "pace": 6.00,
                "heart_rate": 155,
                "calories": 450,
                "notes": "힘들었지만 완주함",
                "location": "한강공원",
                "weather": {"temperature": 18, "condition": "흐림"},
                "splits": [
                    {"km": 1, "pace": 5.45, "heart_rate": 150},
                    {"km": 2, "pace": 5.55, "heart_rate": 155},
                    {"km": 3, "pace": 6.00, "heart_rate": 160},
                    {"km": 4, "pace": 6.10, "heart_rate": 162},
                    {"km": 5, "pace": 6.15, "heart_rate": 165},
                    {"km": 6, "pace": 6.20, "heart_rate": 168},
                    {"km": 7, "pace": 6.25, "heart_rate": 170}
                ]
            },
            {
                "id": 3,
                "activity_id": "run_003",
                "user_id": 1,
                "activity_name": "주말 장거리 러닝",
                "start_time_local": "2024-03-23T08:00:00",
                "distance": 15.0,
                "duration": 5400,
                "pace": 6.00,
                "heart_rate": 150,
                "calories": 900,
                "notes": "마라톤 대비 장거리 훈련",
                "location": "북악산 코스",
                "weather": {"temperature": 12, "condition": "맑음"},
                "splits": [
                    {"km": 1, "pace": 5.30, "heart_rate": 145},
                    {"km": 2, "pace": 5.40, "heart_rate": 148},
                    {"km": 3, "pace": 5.50, "heart_rate": 150},
                    {"km": 4, "pace": 6.00, "heart_rate": 152},
                    {"km": 5, "pace": 6.10, "heart_rate": 155},
                    {"km": 6, "pace": 6.20, "heart_rate": 158},
                    {"km": 7, "pace": 6.30, "heart_rate": 160},
                    {"km": 8, "pace": 6.40, "heart_rate": 162},
                    {"km": 9, "pace": 6.50, "heart_rate": 165},
                    {"km": 10, "pace": 7.00, "heart_rate": 168},
                    {"km": 11, "pace": 7.10, "heart_rate": 170},
                    {"km": 12, "pace": 7.20, "heart_rate": 172},
                    {"km": 13, "pace": 7.30, "heart_rate": 175},
                    {"km": 14, "pace": 7.40, "heart_rate": 178},
                    {"km": 15, "pace": 7.50, "heart_rate": 180}
                ]
            }
        ]

    def get_activity_stats(self):
        # 테스트 데이터 반환
        return {
            "total_distance": 27.7,
            "total_duration": 9900,
            "average_pace": 5.95,
            "total_calories": 1670,
            "weekly_stats": {
                "distance": 27.7,
                "duration": 9900,
                "activities": 3,
                "average_heart_rate": 150,
                "pace_distribution": {
                    "easy": 1,
                    "moderate": 1,
                    "hard": 1
                }
            },
            "monthly_stats": {
                "distance": 85.5,
                "duration": 30600,
                "activities": 9,
                "average_heart_rate": 148,
                "pace_distribution": {
                    "easy": 3,
                    "moderate": 4,
                    "hard": 2
                }
            },
            "pace_distribution": {
                "easy": 1,
                "moderate": 1,
                "hard": 1
            },
            "heart_rate_zones": {
                "zone1": 1800,  # 120-130 bpm
                "zone2": 3600,  # 130-140 bpm
                "zone3": 4200,  # 140-150 bpm
                "zone4": 1800,  # 150-160 bpm
                "zone5": 900    # 160+ bpm
            },
            "training_load": {
                "acute": 85,
                "chronic": 75,
                "fitness": 80,
                "fatigue": 65
            },
            "improvement_metrics": {
                "pace_improvement": -0.5,  # 분/km 단위로 개선
                "distance_increase": 2.5,  # km 단위로 증가
                "endurance_increase": 15   # % 단위로 증가
            }
        }

    def _create_agent(self):
        prompt = PromptTemplate.from_template(
            """당신은 러닝 활동 데이터를 분석하는 AI 어시스턴트입니다.
            사용자의 질문에 답변하기 위해 다음 도구들을 사용할 수 있습니다:
            
            {tools}
            
            사용 가능한 도구들: {tool_names}
            
            질문: {input}
            {agent_scratchpad}
            """
        )
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True
        )

    async def process_query(self, query: str):
        try:
            logger.info(f"Processing query: {query}")
            response = await self.agent.ainvoke({"input": query})
            logger.info(f"Query processed successfully: {response}")
            return response.get("output", "죄송합니다. 응답을 생성하는데 문제가 발생했습니다.")
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# API 엔드포인트
class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        agent = RunningActivityAgent()
        response = await agent.process_query(request.query)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in /query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gcp_initialized": "GOOGLE_APPLICATION_CREDENTIALS" in os.environ,
        "model": "gemini-pro"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 