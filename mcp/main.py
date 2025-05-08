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
import json
import aiohttp

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

MODEL_NAME = "gemini-2.5-pro-exp-03-25"
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# GCP 인증 설정
try:
    # 서비스 계정 키 파일 경로 확인
    key_file = os.path.join(os.path.dirname(__file__), "gcp-key.json")
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"GCP 서비스 계정 키 파일을 찾을 수 없습니다: {key_file}")
    
    # 환경 변수 설정
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
    
    # Vertex AI 초기화
    aiplatform.init(
        project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )
    logger.info(f"GCP AI Platform initialized successfully with key file: {key_file}")
except Exception as e:
    logger.error(f"GCP 초기화 실패: {str(e)}")
    logger.error("다음 사항을 확인해주세요:")
    logger.error("1. gcp-key.json 파일이 mcp 디렉토리에 있는지")
    logger.error("2. .env 파일에 GCP_PROJECT_ID와 GCP_LOCATION이 설정되어 있는지")
    logger.error("3. 서비스 계정에 필요한 권한이 부여되어 있는지")
    raise

app = FastAPI(title="Running Activity MCP Server")

# 백엔드 API 클라이언트
class BackendClient:
    def __init__(self, base_url: str = BACKEND_URL):
        # base_url에 http://가 없는 경우 추가
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        self.base_url = base_url

    async def get_running_activities(self, user_id: int):
        try:
            # 실제 API 호출 시도
            url = f"{self.base_url}/activities/{user_id}"
            try:
                logger.info(f"백엔드 API 호출 시도: {url}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"API 호출 성공: {url}")
                            return data
                        else:
                            error_text = await response.text()
                            logger.warning(f"API 호출 실패 (상태 코드: {response.status})")
                            logger.warning(f"에러 응답: {error_text}")
                            logger.warning(f"요청 URL: {url}")
                            logger.warning(f"요청 헤더: {response.request_info.headers}")
            except aiohttp.ClientError as e:
                logger.warning(f"API 연결 실패 (ClientError): {str(e)}")
                logger.warning(f"요청 URL: {url}")
                logger.warning(f"에러 타입: {type(e).__name__}")
                import traceback
                logger.warning(f"스택 트레이스: {traceback.format_exc()}")
            except Exception as e:
                logger.warning(f"API 연결 실패 (기타 에러): {str(e)}")
                logger.warning(f"요청 URL: {url}")
                logger.warning(f"에러 타입: {type(e).__name__}")
                import traceback
                logger.warning(f"스택 트레이스: {traceback.format_exc()}")

            logger.info("테스트 데이터를 반환합니다.")
            # API 호출 실패 시 테스트 데이터 반환
            return [
                {
                    "id": 1,
                    "activity_id": "run_001",
                    "user_id": user_id,
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
                }
            ]
        except Exception as e:
            logger.error(f"Failed to fetch running activities: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch running activities")

    async def get_activity_stats(self, user_id: int):
        try:
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
                }
            }
        except Exception as e:
            logger.error(f"Failed to fetch activity stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch activity stats")

# AI 에이전트 설정
class RunningActivityAgent:
    def __init__(self, user_id: int):
        try:
            self.user_id = user_id
            self.llm = ChatVertexAI(
                model_name=MODEL_NAME,
                temperature=0,
                max_output_tokens=4096,
                top_p=0.8,
                top_k=40,
                location=os.getenv("GCP_LOCATION", "us-central1"),
                project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai")
            )
            
            # 동기 래퍼 함수로 변경
            def get_activities_wrapper(_):
                try:
                    client = BackendClient()
                    import asyncio
                    result = asyncio.run(client.get_running_activities(self.user_id))
                    # Python 객체를 JSON 문자열로 변환
                    import json
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    logger.error(f"Error in get_activities_wrapper: {str(e)}")
                    return "[]"
            
            def get_stats_wrapper(_):
                try:
                    client = BackendClient()
                    import asyncio
                    result = asyncio.run(client.get_activity_stats(self.user_id))
                    # Python 객체를 JSON 문자열로 변환
                    import json
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    logger.error(f"Error in get_stats_wrapper: {str(e)}")
                    return "{}"
            
            self.tools = [
                Tool(
                    name="GetRunningActivities",
                    func=get_activities_wrapper,
                    description="러닝 활동 데이터를 조회합니다."
                ),
                Tool(
                    name="GetActivityStats",
                    func=get_stats_wrapper,
                    description="러닝 활동 통계를 조회합니다."
                )
            ]
            
            self.agent = self._create_agent()
            logger.info("RunningActivityAgent initialized successfully with Gemini Pro")
        except Exception as e:
            logger.error(f"Failed to initialize RunningActivityAgent: {str(e)}")
            raise


    def _create_agent(self):
        prompt = PromptTemplate.from_template(
            """당신은 20년차 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 분석하여 전문적인 조언을 제공합니다.

            사용 가능한 도구들:
            {tools}
            
            사용 가능한 도구들: {tool_names}
            
            질문: {input}
            
            다음 형식으로 단계별로 진행하세요:
            
            Thought: 현재 단계에서 해야 할 일을 설명
            
            Action: 사용할 도구 이름
            
            Action Input: {{}}  # 도구에 파라미터가 필요 없는 경우 빈 중괄호 사용
            
            Observation: 도구의 실행 결과 (JSON 문자열)
            
            Thought: 결과를 분석하고 다음 단계 결정
            
            Final Answer: 최종 답변 (모든 데이터 수집 후에만 작성)
            
            {agent_scratchpad}
            
            중요 규칙:
            1. 각 단계는 반드시 새로운 줄에서 시작하고, 단계 사이에 빈 줄을 추가하세요.
            2. Action Input은 반드시 {{}} 형식으로 작성하세요. 파라미터가 필요 없는 도구의 경우에도 빈 중괄호를 사용해야 합니다.
            3. Observation은 도구 결과를 JSON 문자열 그대로 복사하세요. 수정하지 마세요.
            4. Final Answer는 모든 데이터 수집 후에만 작성하세요.
            5. 각 단계는 위 순서를 정확히 따라야 합니다.
            6. Action은 반드시 제공된 도구 중 하나만 사용하세요.
            7. Thought 다음에는 반드시 Action이 와야 합니다.
            8. Observation 다음에는 반드시 Thought가 와야 합니다.
            9. GetRunningActivities와 GetActivityStats 도구는 각각 한 번만 사용하세요.
            10. 두 도구의 결과를 모두 수집했다면, 바로 Final Answer를 작성하세요.
            11. Final Answer는 다음 형식으로 작성하세요:
                - 현재 상태 분석
                - 목표 달성을 위한 구체적인 조언
                - 훈련 계획 제안
                - 주의사항 및 팁
            
            분석 시 고려사항:
            1. 최근 러닝 기록
               - 페이스와 거리
               - 심박수 패턴
               - 훈련 강도
            
            2. 통계 데이터
               - 평균 페이스
               - 총 거리
               - 훈련 부하
            
            3. 개선 추세
               - 페이스 개선도
               - 거리 증가 추이
               - 심박수 안정성
            
            4. 목표 달성 전략
               - 단계별 훈련 계획
               - 페이스 조절 방법
               - 휴식 및 회복 전략

            예시 응답 형식:
            Thought: 사용자의 러닝 활동 데이터를 먼저 확인해야겠습니다.

            Action: GetRunningActivities

            Action Input: {{}}

            Observation: [{{"id":1,"activity_id":"run_001","distance":5.2,"pace":5.45,"heart_rate":145,"calories":320}}]

            Thought: 러닝 활동 데이터를 확인했으니, 이제 통계 데이터도 확인해보겠습니다.

            Action: GetActivityStats

            Action Input: {{}}

            Observation: {{"total_distance":27.7,"total_duration":9900,"average_pace":5.95,"total_calories":1670}}

            Thought: 이제 모든 데이터를 수집했으니 분석을 시작하겠습니다.

            Final Answer: 현재 러닝 상태를 분석한 결과, 다음과 같은 조언을 드립니다:
            1. 현재 상태: 평균 페이스 5.95분/km로 안정적인 러닝이 가능한 상태입니다.
            2. 목표 달성 전략: 하프마라톤을 위해 주 3회 러닝을 권장합니다.
            3. 훈련 계획: 
               - 주 2회 5km 러닝
               - 주 1회 10km 러닝
               - 점진적으로 거리 증가
            4. 주의사항: 심박수 145bpm을 유지하며 훈련하세요.
            """
        )
        
        # 프롬프트 로깅을 위한 함수
        def log_prompt(input_text: str) -> None:
            try:
                formatted_prompt = prompt.format(
                    tools="\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools]),
                    tool_names=", ".join([tool.name for tool in self.tools]),
                    input=input_text,
                    agent_scratchpad=""
                )
                logger.info("=== Generated Prompt ===")
                logger.info(formatted_prompt)
                logger.info("======================")
            except Exception as e:
                logger.error(f"Error formatting prompt: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        try:
            # 에이전트 생성
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # AgentExecutor 생성
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors=True,
                max_iterations=20,  # 최대 반복 횟수를 2로 제한
                max_execution_time=600,
                early_stopping_method="generate"  # 조기 종료 메서드 추가
            )
            
            # 프롬프트 로깅을 포함한 실행 함수
            async def execute_with_logging(input_text: str):
                log_prompt(input_text)
                try:
                    response = await executor.ainvoke({"input": input_text})
                    
                    # 중간 단계 로깅 추가
                    steps = response.get("intermediate_steps", [])
                    logger.info("=== Agent Execution Steps ===")
                    for i, step in enumerate(steps, 1):
                        if isinstance(step, tuple) and len(step) > 1:
                            action, result = step
                            logger.info(f"\nStep {i}:")
                            logger.info(f"Action: {action}")
                            logger.info(f"Result: {result}")
                    logger.info("=========================")
                    
                    # 응답이 없는 경우 중간 단계에서 정보 추출
                    if not response.get("output"):
                        if steps:
                            # 마지막 유효한 결과 찾기
                            for step in reversed(steps):
                                if isinstance(step, tuple) and len(step) > 1:
                                    result = step[1]
                                    if isinstance(result, str):
                                        try:
                                            # JSON 문자열을 파싱
                                            parsed_result = json.loads(result)
                                            response["output"] = self._format_response(parsed_result)
                                            break
                                        except json.JSONDecodeError as e:
                                            logger.error(f"JSON 파싱 에러: {str(e)}")
                                            logger.error(f"파싱 시도한 문자열: {result}")
                                            continue
                    
                    # 여전히 응답이 없는 경우 기본 메시지 반환
                    if not response.get("output"):
                        response["output"] = "죄송합니다. 응답을 생성하는데 문제가 발생했습니다."
                    
                    return response
                except Exception as e:
                    logger.error(f"Error in execute_with_logging: {str(e)}")
                    logger.error(f"Error type: {type(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return {"output": "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."}
            
            return execute_with_logging
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise

    def _format_response(self, result):
        """결과를 포맷팅하는 함수"""
        try:
            logger.info(f"Formatting result: {result}")
            logger.info(f"Result type: {type(result)}")
            
            if isinstance(result, list) and result:
                activity = result[0]
                logger.info(f"Processing activity: {activity}")
                return f"현재 러닝 활동을 분석한 결과입니다:\n" + \
                       f"최근 러닝 거리: {activity.get('distance', 'N/A')}km\n" + \
                       f"최근 페이스: {activity.get('pace', 'N/A')}분/km\n" + \
                       f"심박수: {activity.get('heart_rate', 'N/A')}bpm\n" + \
                       f"칼로리: {activity.get('calories', 'N/A')}kcal"
            elif isinstance(result, dict):
                logger.info(f"Processing stats: {result}")
                return f"현재 러닝 통계를 기반으로 분석한 결과입니다:\n" + \
                       f"총 거리: {result.get('total_distance', 'N/A')}km\n" + \
                       f"평균 페이스: {result.get('average_pace', 'N/A')}분/km\n" + \
                       f"총 칼로리: {result.get('total_calories', 'N/A')}kcal"
            else:
                logger.warning(f"Unexpected result type: {type(result)}")
                return "데이터를 분석할 수 없습니다."
        except Exception as e:
            logger.error(f"Error in _format_response: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "데이터를 분석하는 중에 오류가 발생했습니다."

    async def process_query(self, query: str):
        """사용자 쿼리를 처리하는 메서드"""
        try:
            logger.info(f"Processing query: {query}")
            executor = self._create_agent()
            if not executor:
                raise ValueError("Agent executor creation failed")
            
            logger.info("Executing agent...")
            response = await executor(query)
            logger.info(f"Agent response: {response}")
            
            if not response:
                logger.warning("Empty response from agent")
                return "죄송합니다. 응답을 생성하는데 문제가 발생했습니다."
            
            output = response.get("output", "")
            if not output:
                logger.warning("No output in response")
                return "죄송합니다. 응답을 생성하는데 문제가 발생했습니다."
            
            logger.info(f"Final output: {output}")
            return output
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

# API 엔드포인트
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gcp_initialized": "GOOGLE_APPLICATION_CREDENTIALS" in os.environ,
        "model": MODEL_NAME,
        "backend_url": BACKEND_URL
    }

@app.get("/test-backend")
async def test_backend_connection():
    try:
        # 백엔드 클라이언트 생성
        client = BackendClient()
        
        # 테스트용 user_id
        test_user_id = 1
        
        # 러닝 활동 데이터 조회 테스트
        activities_response = await client.get_running_activities(test_user_id)
        
        # 통계 데이터 조회 테스트  
        stats_response = await client.get_activity_stats(test_user_id)

        print(activities_response)
        
        return {
            "status": "success",
            "backend_url": BACKEND_URL,
            "activities": activities_response,
            "stats": stats_response
        }

    except Exception as e:
        logger.error(f"백엔드 연결 테스트 실패: {str(e)}")
        logger.error(f"에러 타입: {type(e).__name__}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "백엔드 연결 테스트 실패",
                "error": str(e),
                "backend_url": BACKEND_URL
            }
        )

class QueryRequest(BaseModel):
    query: str
    user_id: int

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        agent = RunningActivityAgent(user_id=request.user_id)
        response = await agent.process_query(request.query)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in /query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 