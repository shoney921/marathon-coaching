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
from ..providers.tools_manager import ToolManager
import asyncio
import json

logger = logging.getLogger(__name__)

class AIProvider:
    def __init__(self):
        self.model_name = "gemini-2.5-pro-exp-03-25"
        self._initialize_vertex_ai()
        self.llm = self._create_llm()
        self.backend_provider = BackendProvider()
        self.tool_manager = ToolManager(self.backend_provider)

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

    """
    1. analyze_activity
    사용자가 선택한 특정 러닝 활동 데이터를 분석하여 맞춤형 피드백을 제공합니다.
    """
    async def analyze_activity(self, user_id: int, query: str, comments: list[str], laps: list[dict]) -> Dict[str, Any]:
        """러닝 활동 분석"""
        try:
            # 에이전트 생성 및 실행
            tools = self.tool_manager.create_tools(user_id, ["GetRunningActivities", "GetMonthlyActivitySummary"])
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

    def _create_ativity_coaching_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자가 선택한 특정 러닝 활동 데이터를 분석하여 맞춤형 피드백을 제공합니다.
            오늘 날짜는 {today}입니다.

            분석할 활동 데이터:
            {input}

            사용자의 코멘트:
            {comments}

            랩 데이터:
            {laps}

            다음 형식으로 단계별로 진행하세요. 각 단계는 반드시 새로운 줄에서 시작하고, 단계 사이에 빈 줄을 추가하세요:
            
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
            4. Final Answer는 다음 형식으로 간단하게 작성하세요 (300자 이내):
               - 핵심 성과: 선택된 활동에서 가장 눈에 띄는 성과나 개선점
               - 주요 피드백: 선택된 활동을 기반으로 한 가장 중요한 1-2가지 개선 제안
               - 다음 활동을 위한 팁: 선택된 활동의 특성을 고려한 구체적인 조언
            5. 도구는 선택된 활동의 맥락을 이해하기 위한 보조 정보로만 사용하세요.
            6. 분석의 중심은 반드시 선택된 활동 데이터({input})여야 합니다.
            7. 사용자의 코멘트와 랩 데이터를 반드시 고려하여 분석하세요.
            8. 각 단계는 반드시 위의 형식을 정확히 따라야 합니다.
            9. Action 단계는 반드시 제공된 도구 중 하나를 선택해야 합니다.
            10. Final Answer는 모든 데이터 수집이 완료된 후에만 작성하세요.
            """
        )
        
        return create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )

    """
    2. create_race_training
    사용자의 러닝 활동 데이터를 분석하여 대회 일정까지 맞는 훈련 일정을 제공합니다.
    """
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
                tools = self.tool_manager.create_tools(user_id, ["GetRunningActivities", "GetMonthlyActivitySummary"])
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

    """
    3. running_coach_prompt
    사용자의 러닝 활동 데이터를 분석하여 러닝 코치 응답을 생성합니다.
    """
    async def running_coach_prompt(
        self,
        user_id: int,
        user_message: str,
        chat_history: list[dict],
    ) -> Dict[str, Any]:
        """러닝 코치 응답 생성"""
        try:
            # 에이전트 생성 및 실행
            tools = self.tool_manager.create_tools(user_id, [
                "GetRunningActivities", 
                "GetMonthlyActivitySummary",
                "GetSchedules",
                "UpdateSchedule"
            ])
            agent = self._create_generate_running_coach_agent(tools)
            executor = self._create_executor(agent, tools)
            
            response = await executor.ainvoke({
                "today": datetime.now().strftime("%Y-%m-%d"),
                "input": user_message,
                "chat_history": chat_history
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
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 분석하고 훈련 일정을 관리합니다.
            오늘 날짜는 {today}입니다.

            사용자의 요청:
            {input}

            사용자와 이전 대화 내역:
            {chat_history}
            
            다음 형식으로 단계별로 진행하세요. 각 단계는 반드시 새로운 줄에서 시작하고, 단계 사이에 빈 줄을 추가하세요:
            
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
            
            도구 사용 가이드라인:
            1. 활동 데이터 조회 도구 (GetRunningActivities)
               - 사용자의 최근 활동 데이터를 조회할 때 사용
               - 훈련 강도와 빈도를 분석할 때 사용
               - 부상 위험을 평가할 때 사용

            2. 월간 활동 분석 도구 (GetMonthlyActivitySummary)
               - 사용자의 월간 활동 패턴을 파악할 때 사용
               - 월간 활동 목표를 설정할 때 사용
               - 월간 활동 성과를 평가할 때 사용

            3. 일정 조회 도구 (GetSchedules)
               - 현재 훈련 일정을 확인할 때 사용
               - 일정 충돌을 확인할 때 사용

            4. 일정 수정 도구 (UpdateSchedule)
               - 훈련 강도 조절이 필요할 때 사용
               - 훈련 일정 최적화가 필요할 때 사용
               - 부상 예방을 위한 일정 조정이 필요할 때 사용
            
            중요 규칙:
            1. 각 단계는 반드시 새로운 줄에서 시작하고, 단계 사이에 빈 줄을 추가하세요.
            2. Action Input은 반드시 {{}} 형식으로 작성하세요.
            3. Observation은 도구 결과를 JSON 문자열 그대로 복사하세요.
            4. Final Answer는 다음 형식으로 작성하세요:
               - 활동 분석: 사용자의 러닝 활동 데이터 분석 결과
               - 훈련 제안: 현재 상태를 고려한 훈련 계획 제안
               - 일정 관리: 필요한 경우 훈련 일정 수정 제안
            5. 일정 수정이 필요한 경우, UpdateSchedule 도구를 사용하여 구체적인 수정 사항을 제안하세요.
            6. 일정 수정 시 다음 형식을 정확히 따라주세요:
               {{
                   "id": "수정할 일정의 ID",
                   "title": "수정된 제목",
                   "schedule_datetime": "YYYY-MM-DDTHH:mm:ss",
                   "description": "수정된 설명",
                   "type": "훈련 또는 대회"
               }}
            7. 각 단계는 반드시 위의 형식을 정확히 따라야 합니다.
            8. Action 단계는 반드시 제공된 도구 중 하나를 선택해야 합니다.
            9. Final Answer는 모든 데이터 수집이 완료된 후에만 작성하세요.
            10. 일정 수정은 사용자의 현재 상태와 목표를 고려하여 합리적인 범위 내에서 제안하세요.

            컨텍스트 유지 규칙:
            1. 이전 대화에서 언급된 중요 정보는 반드시 참조
            2. 사용자의 목표와 현재 상태를 지속적으로 고려
            3. 일관된 훈련 방향성 유지
            4. 부상 위험을 지속적으로 모니터링
            5. 사용자의 피드백을 다음 대화에서 반영

            에러 처리 규칙:
            1. 도구 실행 실패 시
               - 대체 방안 제시
               - 사용자에게 명확한 설명 제공
               - 다음 단계 제안

            2. 데이터 부족 시
               - 추가 정보 요청
               - 일반적인 가이드라인 제공
               - 안전한 범위 내에서 조언

            3. 일정 충돌 시
               - 우선순위 설정
               - 대체 일정 제안
               - 사용자와 협의 필요성 판단
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