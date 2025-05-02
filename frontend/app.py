import streamlit as st
import requests
import json
from datetime import datetime
import os

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# 페이지 설정
st.set_page_config(
    page_title="마라톤 코칭 시스템",
    page_icon="🏃",
    layout="wide"
)

# 세션 상태 초기화
if 'user' not in st.session_state:
    st.session_state.user = None

# 로그인 체크
if not st.session_state.user:
    st.switch_page("pages/login.py")

# 공통 함수
def get_user_data():
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return None

def get_training_logs():
    try:
        response = requests.get(
            f"{API_BASE_URL}/training-logs/user/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return []

def get_sleep_logs():
    try:
        response = requests.get(
            f"{API_BASE_URL}/sleep-logs/user/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return []

def get_feedback(feedback_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/feedback/{feedback_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return None

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["홈", "훈련 로그", "수면 로그", "AI 코칭"])

# 홈 페이지
with tab1:
    print("## st.session_state.user")
    print(st.session_state.user)
    print("## st.session_state.user['username']")
    print(st.session_state.user['username'])
    st.title(f"🏃 {st.session_state.user['username']}님, 환영합니다!")
    
    # 사용자 정보 표시
    user_data = get_user_data()
    if user_data:
        st.subheader("내 정보")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"이름: {user_data['username']}")
            st.write(f"이메일: {user_data['email']}")
            st.write(f"나이: {user_data['age']}세")
        with col2:
            st.write(f"체중: {user_data['weight']}kg")
            st.write(f"키: {user_data['height']}cm")
            st.write(f"목표 대회: {user_data['target_race']}")
            st.write(f"목표 시간: {user_data['target_time']}")
    
    # 로그아웃 버튼
    if st.button("로그아웃"):
        st.session_state.user = None
        st.rerun()

# 훈련 로그 페이지
with tab2:
    st.title("🏃 훈련 로그")
    
    # 새 훈련 로그 등록
    with st.expander("새 훈련 로그 등록"):
        with st.form("training_form"):
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
                    "user_id": st.session_state.user['id'],
                    "date": datetime.combine(date, time).isoformat(),
                    "distance": distance,
                    "duration": duration,
                    "pace": pace,
                    "heart_rate": heart_rate if heart_rate else None,
                    "notes": notes if notes else None
                }
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/training-logs/",
                        json=log_data,
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if response.status_code == 200:
                        st.success("훈련 로그가 성공적으로 등록되었습니다!")
                    else:
                        st.error(f"훈련 로그 등록에 실패했습니다. (상태 코드: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    st.error(f"API 연결 오류: {str(e)}")
    
    # 훈련 로그 목록 표시
    st.subheader("훈련 로그 목록")
    training_logs = get_training_logs()
    if training_logs:
        for log in training_logs:
            with st.expander(f"{log['date']} - {log['distance']}km"):
                st.write(f"소요 시간: {log['duration']}분")
                st.write(f"페이스: {log['pace']}분/km")
                if log['heart_rate']:
                    st.write(f"심박수: {log['heart_rate']}")
                if log['notes']:
                    st.write(f"메모: {log['notes']}")
    else:
        st.info("등록된 훈련 로그가 없습니다.")

# 수면 로그 페이지
with tab3:
    st.title("😴 수면 로그")
    
    # 새 수면 로그 등록
    with st.expander("새 수면 로그 등록"):
        with st.form("sleep_form"):
            date = st.date_input("수면 날짜")
            duration = st.number_input("수면 시간 (시간)", min_value=0.0, max_value=24.0)
            quality = st.slider("수면 품질 (1-10)", min_value=1, max_value=10)
            notes = st.text_area("메모 (선택사항)")
            
            submitted = st.form_submit_button("등록")
            if submitted:
                log_data = {
                    "user_id": st.session_state.user['id'],
                    "date": datetime.combine(date, datetime.min.time()).isoformat(),
                    "duration": duration,
                    "quality": quality,
                    "notes": notes if notes else None
                }
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/sleep-logs/",
                        json=log_data,
                        headers={"Authorization": f"Bearer {st.session_state.user['token']}"}
                    )
                    if response.status_code == 200:
                        st.success("수면 로그가 성공적으로 등록되었습니다!")
                    else:
                        st.error(f"수면 로그 등록에 실패했습니다. (상태 코드: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    st.error(f"API 연결 오류: {str(e)}")
    
    # 수면 로그 목록 표시
    st.subheader("수면 로그 목록")
    sleep_logs = get_sleep_logs()
    if sleep_logs:
        for log in sleep_logs:
            with st.expander(f"{log['date']} - {log['duration']}시간"):
                st.write(f"수면 품질: {log['quality']}/10")
                if log['notes']:
                    st.write(f"메모: {log['notes']}")
    else:
        st.info("등록된 수면 로그가 없습니다.")

# AI 코칭 페이지
with tab4:
    st.title("🤖 AI 코칭")
    
    # AI 코칭 요청
    with st.expander("AI 코칭 요청"):
        if st.button("AI 코칭 요청"):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/request-coaching/{st.session_state.user['id']}",
                    headers={"Authorization": f"Bearer {st.session_state.user['token']}"}
                )
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