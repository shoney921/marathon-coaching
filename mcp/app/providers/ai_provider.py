import os
import logging
from typing import Dict, Any
from datetime import datetime
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from google.cloud import aiplatform
from ..providers.backend_provider import BackendProvider
import asyncio

logger = logging.getLogger(__name__)

class AIProvider:
    def __init__(self):
        self.model_name = "gemini-2.5-pro-exp-03-25"
        self._initialize_vertex_ai()
        self.llm = self._create_llm()
        self.backend_provider = BackendProvider()

    def _initialize_vertex_ai(self):
        """Vertex AI 초기화"""
        try:
            key_file = os.path.join(os.path.dirname(__file__), "..", "..", "gcp-key.json")
            if not os.path.exists(key_file):
                raise FileNotFoundError(f"GCP 서비스 계정 키 파일을 찾을 수 없습니다: {key_file}")
            
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
            
            aiplatform.init(
                project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai"),
                location=os.getenv("GCP_LOCATION", "us-central1")
            )
            logger.info("Vertex AI 초기화 성공")
        except Exception as e:
            logger.error(f"Vertex AI 초기화 실패: {str(e)}")
            raise

    def _create_llm(self) -> ChatVertexAI:
        """LLM 인스턴스 생성"""
        return ChatVertexAI(
            model_name=self.model_name,
            temperature=0,
            max_output_tokens=4096,
            top_p=0.8,
            top_k=40,
            location=os.getenv("GCP_LOCATION", "us-central1"),
            project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai")
        )

    async def analyze_activity(self, user_id: int, query: str) -> Dict[str, Any]:
        """러닝 활동 분석"""
        try:
            # 에이전트 생성 및 실행
            tools = await self._create_tools(user_id)
            agent = self._create_agent(tools)
            executor = self._create_executor(agent, tools)
            
            response = await executor.ainvoke({
                "input": query,
                "today": datetime.now().strftime("%Y-%m-%d")
            })
            
            return {
                "analysis": response.get("output", ""),
                "metadata": {
                    "model": self.model_name,
                    "user_id": user_id
                }
            }
        except Exception as e:
            logger.error(f"활동 분석 실패: {str(e)}")
            raise

    async def _create_tools(self, user_id: int) -> list[Tool]:
        """에이전트 도구 생성"""
        async def get_activities_wrapper(_):
            try:
                result = await self.backend_provider.get_running_activities(user_id)
                import json
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_activities_wrapper: {str(e)}")
                return "[]"
        
        async def get_monthly_summary_wrapper(_):
            try:
                result = await self.backend_provider.get_monthly_activity_summary(user_id)
                import json
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_monthly_summary_wrapper: {str(e)}")
                return "{}"
        
        # 비동기 함수를 동기 함수로 래핑
        def sync_get_activities(_):
            return asyncio.run(get_activities_wrapper(_))
            
        def sync_get_monthly_summary(_):
            return asyncio.run(get_monthly_summary_wrapper(_))
        
        return [
            Tool(
                name="GetRunningActivities",
                func=sync_get_activities,
                description="모든 러닝 활동 데이터를 조회합니다. 러닝 활동 데이터는 러닝 활동 이름, 시작 시간, 거리, 소요시간, 페이스, 심박수, 칼로리, 위치, 날씨, 노트 등의 정보를 포함합니다."
            ),
            Tool(
                name="GetMonthlyActivitySummary",
                func=sync_get_monthly_summary,
                description="러닝 활동 월간 통계를 조회합니다. 월별 거리, 소요시간, 평균 페이스를 조회합니다."
            )
        ]

    def _create_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 20년차 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 분석하여 질문에 대한 전문적인 조언을 제공합니다.
            오늘 날짜는 {today}입니다. 조회한 데이터들의 시간 순서들도 잘 고려해서 질문의 답변을 해주세요. 
            심박수, 파워, 케이던스, 속도, 거리, 시간 등 모든 데이터를 참고하여 질문에 대한 답변을 해주세요.
            
            사용 가능한 도구들: {tool_names}

            사용 가능한 도구들의 설명:
            {tools}
            
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
            9. GetRunningActivities와 GetMonthlyActivitySummary 도구는 각각 한 번만 사용하세요.
            10. 두 도구의 결과를 모두 수집했다면, 바로 Final Answer를 작성하세요.
            11. Final Answer는 다음 형식으로 작성하세요:
                - 현재 상태 분석
                - 목표 달성을 위한 구체적인 조언
                - 훈련 계획 제안
                - 주의사항 및 팁
            """
        )
        
        return create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )

    def _create_executor(self, agent, tools: list[Tool]):
        """에이전트 실행기 생성"""
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=5,  # 반복 횟수 조정
            max_execution_time=300,  # 5분으로 제한
        ) 