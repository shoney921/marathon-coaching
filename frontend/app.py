import streamlit as st
import requests
import json
from datetime import datetime
import os

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# 페이지 설정
st.set_page_config(
    page_title="마라톤 코칭 시스템",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="collapsed"
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

def get_activities_laps():
    try:
        response = requests.get(
            f"{API_BASE_URL}/activities/laps/user/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return []

# 탭 생성
tab1, tab5 = st.tabs(["홈", "활동 기록"])

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

# 활동 기록 페이지
with tab5:
    st.title("🏃 활동 기록")
    
    # 활동 기록 목록 표시
    activities = get_activities_laps()
    if activities:
        for activity in activities:
            # 날짜 형식 변환
            activity_date = datetime.fromisoformat(activity['local_start_time'].replace('Z', '+00:00'))
            formatted_date = activity_date.strftime('%Y년 %m월 %d일 - %H시 %M분')
            
            with st.expander(f"[{formatted_date}][{activity['activity_name']}]         ({activity['distance']}km - {activity['duration']})"):
                st.subheader(f"{activity['activity_name']} - {formatted_date}")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"총 거리: {activity['distance']}km")
                    st.write(f"소요 시간: {activity['duration']}")
                    st.write(f"평균 페이스: {activity['average_pace']}")
                    st.write(f"최대 페이스: {activity['max_pace']}")
                with col2:
                    st.write(f"평균 심박수: {activity['average_hr']} bpm")
                    st.write(f"최대 심박수: {activity['max_hr']} bpm")
                    st.write(f"평균 케이던스: {activity['average_cadence']} spm")
                
                # 랩 데이터 표
                st.write("##### 랩 기록")
                if activity['laps']:
                    lap_data = []
                    for lap in activity['laps']:
                        lap_data.append({
                            "랩 번호": lap['lap_index'],
                            "거리 (km)": lap['distance'],
                            "소요 시간": lap['duration'],
                            "평균 페이스": lap['average_pace'],
                            "평균 심박수 (bpm)": lap['average_hr'],
                            "평균 케이던스 (spm)": lap['average_run_cadence']
                        })
                    st.dataframe(lap_data, hide_index=True)
                else:
                    st.write("랩 데이터가 없습니다.")
    else:
        st.info("등록된 활동 기록이 없습니다.") 