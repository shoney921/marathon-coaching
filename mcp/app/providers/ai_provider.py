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
            max_output_tokens=4096,  # 토큰 수 제한
            top_p=0.8,
            top_k=40,
            project=os.getenv("GCP_PROJECT_ID", "lge-vs-genai")
        )

    async def analyze_activity(self, user_id: int, query: str, comments: list[str], laps: list[dict]) -> Dict[str, Any]:
        """러닝 활동 분석"""
        try:
            # 에이전트 생성 및 실행
            tools = await self._create_tools(user_id)
            agent = self._create_ativity_coaching_agent(tools)
            executor = self._create_executor(agent, tools)
            
            response = await executor.ainvoke({
                "input": query,
                "comments": comments,
                "laps": laps,
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
                logger.info("GetRunningActivities 도구 실행 시작")
                result = await self.backend_provider.get_running_activities(user_id)
                logger.info(f"GetRunningActivities 결과: {result}")
                import json
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_activities_wrapper: {str(e)}")
                return "[]"
        
        async def get_monthly_summary_wrapper(_):
            try:
                logger.info("GetMonthlyActivitySummary 도구 실행 시작")
                result = await self.backend_provider.get_monthly_activity_summary(user_id)
                logger.info(f"GetMonthlyActivitySummary 결과: {result}")
                import json
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error in get_monthly_summary_wrapper: {str(e)}")
                return "{}"
        
        # 비동기 함수를 동기 함수로 래핑
        def sync_get_activities(_):
            try:
                logger.info("sync_get_activities 시작")
                loop = asyncio.get_event_loop()
            except RuntimeError:
                logger.info("새로운 이벤트 루프 생성")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            logger.info("get_activities_wrapper 실행")
            return loop.run_until_complete(get_activities_wrapper(_))
            
        def sync_get_monthly_summary(_):
            try:
                logger.info("sync_get_monthly_summary 시작")
                loop = asyncio.get_event_loop()
            except RuntimeError:
                logger.info("새로운 이벤트 루프 생성")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            logger.info("get_monthly_summary_wrapper 실행")
            return loop.run_until_complete(get_monthly_summary_wrapper(_))
        
        logger.info("도구 생성 시작")
        tools = [
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
        logger.info("도구 생성 완료")
        return tools

    def _create_ativity_coaching_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 간단하고 명확하게 분석하여 핵심적인 피드백을 제공합니다.
            오늘 날짜는 {today}입니다.

            다음 형식으로 단계별로 진행하세요:
            
            Thought: 현재 단계에서 해야 할 일을 설명
            
            Action: 사용할 도구 이름 (반드시 제공된 도구 중 하나를 선택)
            
            Action Input: {{}}  # 도구에 파라미터가 필요 없는 경우 빈 중괄호 사용
            
            Observation: 도구의 실행 결과 (JSON 문자열)
            
            Thought: 결과를 분석하고 다음 단계 결정
            
            Final Answer: 최종 답변 (모든 데이터 수집 후에만 작성)
            
            사용 가능한 도구들: {tool_names}

            사용 가능한 도구들의 설명:
            {tools}
            
            {agent_scratchpad}
            
            중요 규칙:
            1. 각 단계는 반드시 새로운 줄에서 시작하고, 단계 사이에 빈 줄을 추가하세요.
            2. Action Input은 반드시 {{}} 형식으로 작성하세요.
            3. Observation은 도구 결과를 JSON 문자열 그대로 복사하세요.
            4. Final Answer는 다음 형식으로 간단하게 작성하세요 (500자 이내):
               - 핵심 성과: 가장 눈에 띄는 성과나 개선점
               - 주요 피드백: 가장 중요한 1-2가지 개선 제안
               - 다음 활동을 위한 팁: 즉시 적용할 수 있는 구체적인 조언
            """
        )
        
        return create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
    
    async def create_race_training(
        self,
        user_id: int,
        race_name: str,
        race_date: str,
        race_type: str,
        race_time: str,
        special_notes: str
    ) -> Dict[str, Any]:
        """대회 훈련 일정 생성"""
        max_retries = 3
        retry_delay = 2  # 초 단위
        
        for attempt in range(max_retries):
            try:
                logger.info(f"훈련 일정 생성 시도 {attempt + 1}/{max_retries}")
                
                # 에이전트 생성 및 실행
                tools = await self._create_tools(user_id)
                logger.info("도구 생성 완료")
                
                agent = self._create_race_training_agent(tools)
                logger.info("에이전트 생성 완료")
                
                executor = self._create_executor(agent, tools)
                logger.info("실행기 생성 완료")
                
                logger.info("에이전트 실행 시작")
                response = await executor.ainvoke({
                    "today": datetime.now().strftime("%Y-%m-%d"),
                    "race_name": race_name,
                    "race_date": race_date,
                    "race_type": race_type,
                    "race_time": race_time,
                    "special_notes": special_notes
                })
                logger.info("에이전트 실행 완료")
                
                return {
                    "training_schedule": response.get("output", ""),
                    "metadata": {
                        "model": self.model_name,
                        "user_id": user_id
                    }
                }
            except Exception as e:
                error_message = str(e)
                logger.error(f"훈련 일정 생성 시도 {attempt + 1} 실패: {error_message}")
                
                if "429" in error_message and attempt < max_retries - 1:
                    logger.info(f"{retry_delay}초 후 재시도...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                    continue
                else:
                    raise Exception(f"훈련 일정 생성 실패 (시도 {attempt + 1}/{max_retries}): {error_message}")

    #대회 날짜를 보고 훈련 일정을 짜주는 에이전트
    def _create_race_training_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        logger.info("훈련 일정 에이전트 생성 시작")
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 분석하여 대회 일정까지 맞는 훈련 일정을 제공합니다.
            최대한 목표시간을 맞추는 훈련 일정을 제공합니다.
            오늘 날짜: {today}
            대회명: {race_name}
            대회 날짜: {race_date}
            대회 유형: {race_type}
            목표 시간: {race_time}

            다음 형식으로 진행하세요:
            Thought: 현재 단계 설명
            Action: 사용할 도구 선택
            Action Input: {{}}
            Observation: 도구 결과
            Thought: 결과 분석
            Final Answer: 최종 답변

            사용 가능한 도구들: {tool_names}
            도구 설명: {tools}
            특이사항: {special_notes}
            
            {agent_scratchpad}
            
            중요 규칙:
            1. 각 단계는 새 줄에서 시작
            2. Action Input은 {{}} 형식 사용
            3. Observation은 JSON 문자열 그대로 복사
            4. Final Answer는 다음 JSON 형식으로 작성:
            {{
                "schedules": [
                    {{
                        "id": 1,
                        "title": "[5km] 기초 체력 훈련",
                        "datetime": "2025-06-01T08:00:00",
                        "description": "총 거리: 5km\n총 시간: 30분\n목표 페이스: 6:00/km\n훈련 내용: 1) 5분 워밍업\n2) 3km 페이스 6:00/km\n3) 1km 페이스 5:45/km\n4) 1km 페이스 5:30/km\n5) 5분 쿨다운",
                        "type": "훈련"
                    }}
                ]
            }}
            
            훈련 일정 작성 원칙:
            1. 구체적이고 실행 가능한 일정
            2. 사용자 수준에 맞는 난이도
            3. 점진적 부하 증가
            4. 충분한 휴식 시간 확보 (휴식은 일정에 포함하지 않음)
            
            훈련 설명 필수 항목:
            1. 워밍업/쿨다운 시간
            2. 구간별 페이스
            
            훈련 유형:
            - 훈련: 기초 체력, 지구력, 스피드 향상
            - 대회: 대회 페이스 연습, 시뮬레이션
            
            주의사항:
            1. 휴식일은 일정에 포함하지 않습니다.
            2. 훈련 일정 사이에 자동으로 휴식일이 배치됩니다.
            3. 대회 전날은 반드시 휴식일로 지정하되, 일정에는 포함하지 않습니다.
            """
        )
        
        logger.info("에이전트 생성 완료")
        return create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )

    async def generate_running_coach_response(
        self,
        user_id: int,
        user_message: str,
        chat_history: list[dict],
        activities: list[dict],
        training_schedule: list[dict]
    ) -> Dict[str, Any]:
        """러닝 코치 응답 생성"""
        try:
            # 에이전트 생성 및 실행
            tools = await self._create_tools(user_id)
            agent = self._create_generate_running_coach_agent(tools)
            executor = self._create_executor(agent, tools)
            
            response = await executor.ainvoke({
                "today": datetime.now().strftime("%Y-%m-%d"),
                "input": user_message,
                "chat_history": chat_history,
                "activities": activities,
                "training_schedule": training_schedule
            })
            
            return {
                "response": response.get("output", ""),
                "metadata": {
                    "model": self.model_name,
                    "user_id": user_id
                }
            }
        except Exception as e:
            logger.error(f"러닝 코치 응답 생성 실패: {str(e)}")
            raise

    def _create_generate_running_coach_agent(self, tools: list[Tool]):
        """러닝 코치 응답 생성 에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 친근하고 전문적인 러닝 코치입니다. 사용자와 자연스러운 대화를 통해 러닝에 대한 조언을 제공합니다.
            오늘 날짜: {today}

            사용자 컨텍스트:
            - 활동 이력: {activities}
            - 훈련 계획: {training_schedule}
            - 이전 대화: {chat_history}

            사용 가능한 도구들: {tool_names}
            도구 설명: {tools}
            
            현재 질문: {input}
            
            대화 진행 방식:
            1. Thought: 현재 상황 분석
            2. Action: 필요한 도구 선택
            3. Action Input: {{}}
            4. Observation: 도구 결과
            5. Thought: 결과 분석
            6. Final Answer: 친근한 답변
            
            {agent_scratchpad}
            
            대화 규칙:
            1. 친근하고 자연스러운 톤으로 대화하세요
            2. 사용자의 활동 이력과 훈련 계획을 참고하여 맞춤형 조언을 제공하세요
            3. 이전 대화 내용을 기억하고 연속성 있게 답변하세요
            4. 구체적인 수치와 예시를 포함하되, 너무 전문적인 용어는 피하세요
            5. 안전과 건강을 최우선으로 고려하세요
            6. 답변은 200자 이내로 간단명료하게 작성하세요
            7. 사용자의 수준에 맞는 조언을 제공하세요
            8. 긍정적이고 격려하는 톤을 유지하세요
            9. 필요할 때만 도구를 사용하고, 간단한 질문은 바로 답변하세요
            10. 대화의 맥락을 유지하면서 자연스럽게 이어가세요

            답변 예시:
            "안녕하세요! 지난번 5km 러닝 기록을 보니 페이스가 많이 좋아졌네요. 
            이번 주 훈련 계획에 따르면 내일은 8km 러닝이 예정되어 있는데, 
            지난번보다 조금 더 여유로운 페이스로 시작해보는 건 어떨까요? 
            워밍업을 충분히 하고, 첫 2km는 편안한 페이스로 시작하면 좋을 것 같아요."
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
            max_iterations=10,  # 최대 반복 횟수 감소
            max_execution_time=300,  # 실행 시간 제한 감소
            early_stopping_method="force"
        ) 