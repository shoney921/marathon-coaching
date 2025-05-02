import streamlit as st
import requests
import json
from datetime import datetime
import os

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

# 페이지 설정
st.set_page_config(
    page_title="마라톤 코칭 시스템",
    page_icon="🏃",
    layout="wide"
)

# 사이드바 설정
st.sidebar.title("마라톤 코칭 시스템")
page = st.sidebar.radio(
    "메뉴 선택",
    ["홈", "사용자 관리", "훈련 로그", "수면 로그", "AI 코칭"]
)

# 공통 함수
def get_users():
    try:
        response = requests.get(f"{API_BASE_URL}/users/")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return []

def get_feedback(feedback_id):
    try:
        response = requests.get(f"{API_BASE_URL}/feedback/{feedback_id}")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return None

# 홈 페이지
if page == "홈":
    st.title("🏃 마라톤 코칭 시스템에 오신 것을 환영합니다!")
    st.write("""
    이 시스템은 마라톤 훈련을 위한 종합적인 코칭 솔루션을 제공합니다.
    
    주요 기능:
    - 사용자 정보 관리
    - 훈련 로그 기록
    - 수면 패턴 분석
    - AI 기반 개인화된 코칭
    """)

# 사용자 관리 페이지
elif page == "사용자 관리":
    st.title("👤 사용자 관리")
    
    # 새 사용자 등록
    with st.expander("새 사용자 등록"):
        with st.form("user_form"):
            username = st.text_input("사용자 이름")
            email = st.text_input("이메일")
            age = st.number_input("나이", min_value=1, max_value=100)
            weight = st.number_input("체중 (kg)", min_value=0.0)
            height = st.number_input("키 (cm)", min_value=0.0)
            target_race = st.text_input("목표 대회")
            target_time = st.text_input("목표 시간 (HH:MM:SS)")
            
            submitted = st.form_submit_button("등록")
            if submitted:
                user_data = {
                    "username": username,
                    "email": email,
                    "age": age,
                    "weight": weight,
                    "height": height,
                    "target_race": target_race,
                    "target_time": target_time
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/users/", json=user_data)
                    if response.status_code == 200:
                        st.success("사용자가 성공적으로 등록되었습니다!")
                    else:
                        st.error(f"사용자 등록에 실패했습니다. (상태 코드: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    st.error(f"API 연결 오류: {str(e)}")
    
    # 사용자 목록 표시
    st.subheader("사용자 목록")
    users = get_users()
    if users:
        for user in users:
            with st.expander(f"{user['username']} ({user['email']})"):
                st.write(f"나이: {user['age']}세")
                st.write(f"체중: {user['weight']}kg")
                st.write(f"키: {user['height']}cm")
                st.write(f"목표 대회: {user['target_race']}")
                st.write(f"목표 시간: {user['target_time']}")
    else:
        st.info("등록된 사용자가 없습니다.")

# 훈련 로그 페이지
elif page == "훈련 로그":
    st.title("🏃 훈련 로그")
    
    # 새 훈련 로그 등록
    with st.expander("새 훈련 로그 등록"):
        with st.form("training_form"):
            user_id = st.number_input("사용자 ID", min_value=1)
            date = st.date_input("훈련 날짜")
            time = st.time_input("훈련 시간")
            distance = st.number_input("거리 (km)", min_value=0.0)
            duration = st.number_input("소요 시간 (분)", min_value=0)
            pace = st.number_input("페이스 (분/km)", min_value=0.0)
            heart_rate = st.number_input("심박수 (선택사항)", min_value=0)
            notes = st.text_area("메모 (선택사항)")
            
            submitted = st.form_submit_button("등록")
            if submitted:
                log_data = {
                    "user_id": user_id,
                    "date": datetime.combine(date, time).isoformat(),
                    "distance": distance,
                    "duration": duration,
                    "pace": pace,
                    "heart_rate": heart_rate if heart_rate else None,
                    "notes": notes if notes else None
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/training-logs/", json=log_data)
                    if response.status_code == 200:
                        st.success("훈련 로그가 성공적으로 등록되었습니다!")
                    else:
                        st.error(f"훈련 로그 등록에 실패했습니다. (상태 코드: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    st.error(f"API 연결 오류: {str(e)}")

# 수면 로그 페이지
elif page == "수면 로그":
    st.title("😴 수면 로그")
    
    # 새 수면 로그 등록
    with st.expander("새 수면 로그 등록"):
        with st.form("sleep_form"):
            user_id = st.number_input("사용자 ID", min_value=1)
            date = st.date_input("수면 날짜")
            duration = st.number_input("수면 시간 (시간)", min_value=0.0, max_value=24.0)
            quality = st.slider("수면 품질 (1-10)", min_value=1, max_value=10)
            notes = st.text_area("메모 (선택사항)")
            
            submitted = st.form_submit_button("등록")
            if submitted:
                log_data = {
                    "user_id": user_id,
                    "date": datetime.combine(date, datetime.min.time()).isoformat(),
                    "duration": duration,
                    "quality": quality,
                    "notes": notes if notes else None
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/sleep-logs/", json=log_data)
                    if response.status_code == 200:
                        st.success("수면 로그가 성공적으로 등록되었습니다!")
                    else:
                        st.error(f"수면 로그 등록에 실패했습니다. (상태 코드: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    st.error(f"API 연결 오류: {str(e)}")

# AI 코칭 페이지
elif page == "AI 코칭":
    st.title("🤖 AI 코칭")
    
    # AI 코칭 요청
    with st.expander("AI 코칭 요청"):
        user_id = st.number_input("사용자 ID", min_value=1)
        if st.button("AI 코칭 요청"):
            try:
                response = requests.post(f"{API_BASE_URL}/request-coaching/{user_id}")
                if response.status_code == 200:
                    feedback_id = response.json()["feedback_id"]
                    st.success(f"AI 코칭 요청이 성공적으로 제출되었습니다! (피드백 ID: {feedback_id})")
                    
                    # 피드백 결과 확인
                    feedback = get_feedback(feedback_id)
                    if feedback:
                        st.subheader("AI 코칭 피드백")
                        st.write(f"상태: {feedback['status']}")
                        if feedback['feedback']:
                            st.write(f"피드백: {feedback['feedback']}")
                else:
                    st.error(f"AI 코칭 요청에 실패했습니다. (상태 코드: {response.status_code})")
            except requests.exceptions.RequestException as e:
                st.error(f"API 연결 오류: {str(e)}") 