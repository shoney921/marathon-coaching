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
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(get_activities_wrapper(_))
            
        def sync_get_monthly_summary(_):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(get_monthly_summary_wrapper(_))
        
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

    def _create_ativity_coaching_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터, 랩 데이터, 코멘트를 종합적으로 분석하여 맞춤형 피드백을 제공합니다.
            오늘 날짜는 {today}입니다.

            분석해야 할 데이터:
            1. 활동 데이터: {input}
            2. 랩 데이터: {laps}
            3. 사용자 코멘트: {comments}

            사용 가능한 도구들: {tool_names}

            사용 가능한 도구들의 설명:
            {tools}
            
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
            2. Action Input은 반드시 {{}} 형식으로 작성하세요.
            3. Observation은 도구 결과를 JSON 문자열 그대로 복사하세요.
            4. Final Answer는 다음 형식으로 작성하세요:
               a. 활동 개요
                  - 거리, 시간, 페이스 등 기본 정보 요약
                  - 심박수, 케이던스 등 생체 데이터 분석
                  - 랩별 주요 지표 변화 추이
               
               b. 랩 분석
                  - 각 랩의 페이스 변화와 의미
                  - 심박수 구간별 분포와 훈련 강도
                  - 케이던스와 보폭의 변화
                  - 특이사항이 있는 랩의 상세 분석
               
               c. 활동 평가
                  - 목표 대비 성과 분석
                  - 코멘트에 언급된 특이사항 고려
                  - 개선된 점과 부족한 점
                  - 랩 데이터를 통한 훈련 효과 평가
               
               d. 맞춤형 조언
                  - 현재 활동 수준에 맞는 구체적인 개선 방안
                  - 코멘트에 언급된 문제점에 대한 해결책
                  - 랩별 페이스 조절 전략
                  - 다음 활동을 위한 준비사항
               
               e. 주의사항 및 팁
                  - 부상 예방을 위한 주의사항
                  - 훈련 효과를 높이기 위한 팁
                  - 영양 및 회복 관련 조언
                  - 랩 훈련 시 주의할 점

            5. 분석 시 다음 사항을 반드시 고려하세요:
               - 사용자의 코멘트에 언급된 특이사항
               - 랩별 페이스 변화와 그 의미
               - 심박수 구간별 분포와 의미
               - 케이던스와 보폭의 관계
               - 훈련 강도와 회복 필요성
               - 랩 간 휴식 시간의 적절성
               - 전체적인 훈련 패턴과 목표 달성도
               
            6. 답변 작성 시 다음 원칙을 지키세요:
               - 구체적이고 실행 가능한 조언 제공
               - 사용자의 현재 수준에 맞는 난이도로 설명
               - 긍정적인 피드백과 개선점을 균형있게 제시
               - 전문 용어는 쉽게 설명하여 사용
               - 랩 데이터를 통한 객관적인 분석 제공
               - 개인적인 코멘트와 데이터를 연계한 맞춤형 조언
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
        race_time: str
    ) -> Dict[str, Any]:
        """대회 훈련 일정 생성"""
        try:
            # 에이전트 생성 및 실행
            tools = await self._create_tools(user_id)
            agent = self._create_race_training_agent(tools)
            executor = self._create_executor(agent, tools)
            
            response = await executor.ainvoke({
                "today": datetime.now().strftime("%Y-%m-%d"),
                "race_name": race_name,
                "race_date": race_date,
                "race_type": race_type,
                "race_time": race_time
            })
            
            return {
                "training_schedule": response.get("output", ""),
                "metadata": {
                    "model": self.model_name,
                    "user_id": user_id
                }
            }
        except Exception as e:
            logger.error(f"훈련 일정 생성 실패: {str(e)}")
            raise

    #대회 날짜를 보고 훈련 일정을 짜주는 에이전트
    def _create_race_training_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 분석하여 '대회 일정'일 까지 맞는 훈련 일정을 제공해준다.
            오늘 날짜는 {today}입니다. 대회명은 {race_name}입니다. 대회 날짜는 {race_date}입니다.
            {race_type} 대회의 목표 시간은 {race_time}입니다.
            조회한 데이터들의 심박수, 파워, 케이던스, 속도, 거리, 시간 등 모든 데이터를 참고하여 훈련 일정을 작성해주세요.
            
            사용 가능한 도구들: {tool_names}

            사용 가능한 도구들의 설명:
            {tools}
            
            {agent_scratchpad}
            
            1. 훈련 일정 작성 시 다음 사항을 고려하세요:
               - 현재 러닝 능력과 대회까지 남은 기간
               - 주간 훈련 거리와 강도의 점진적 증가
               - 적절한 휴식과 회복 시간 배분
               - 장거리 달리기와 단거리 인터벌의 균형
               - 대회 테이퍼링 기간 설정
               - 코어/근력 훈련 일정 포함
               - 부상 예방을 위한 스트레칭과 회복 운동
            
            2. 일정은 다음 JSON 형식으로 작성하세요:
            {{
                "training_schedule": {{
                    "start_date": "YYYY-MM-DD",
                    "race_date": "YYYY-MM-DD",
                    "race_name": "대회명",
                    "target_pace": "MM:SS/km",
                    "weekly_plans": [
                        {{
                            "week": 1,
                            "total_distance": "주간 목표 거리(km)",
                            "main_focus": "이번 주 중점 사항",
                            "daily_schedule": [
                                {{
                                    "date": "YYYY-MM-DD",
                                    "distance": "거리(km)",
                                    "target_pace": "목표 페이스(MM:SS/km)",
                                    "details": "상세 훈련 내용",
                                    "additional_training": ["스트레칭", "코어운동" 등]
                                }}
                            ],
                            "key_points": [
                                "주요 훈련 포인트1",
                                "주요 훈련 포인트2"
                            ]
                        }}
                    ],
                    "key_points": [
                        "주요 훈련 포인트1",
                        "주요 훈련 포인트2"
                    ],
                    "precautions": [
                        "주의사항1",
                        "주의사항2"
                    ]
                }}
            }}
            
            3. 일정 작성 시 다음 원칙을 지키세요:
               - 구체적이고 실행 가능한 일정 제시
               - 사용자의 현재 수준에 맞는 난이도 설정
               - 점진적 부하 증가 원칙 준수
               - 충분한 휴식과 회복 시간 확보
               - 날씨와 개인 일정을 고려한 유연성 확보
               - 부상 예방을 위한 보조 운동 포함
            """
        )
        
        return create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )


    def _create_ativity_praise_agent(self, tools: list[Tool]):
        """에이전트 생성"""
        prompt = PromptTemplate.from_template(
            """당신은 마라톤 코치 전문가입니다. 사용자의 러닝 활동 데이터를 분석하여 '질문'에 대한 전문적인 조언을 제공합니다.
            오늘 날짜는 {today}입니다. 조회한 데이터들의 시간 순서들도 잘 고려해서 질문의 답변을 해주세요. 
            심박수, 파워, 케이던스, 속도, 거리, 시간 등 모든 데이터를 참고하여 질문에 대한 답변을 해주세요.
            
            사용 가능한 도구들: {tool_names}

            사용 가능한 도구들의 설명:
            {tools}
            
            질문 : {input}
            
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
                - 활동에 대한 분석
                - 활동에 대한 조언
                - 활동에 대한 주의사항 및 팁
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
            max_iterations=20,  # 최대 반복 횟수를 2로 제한
            max_execution_time=600,
            early_stopping_method="generate"  # 조기 종료 메서드 추가
        ) 