import streamlit as st
import requests
from datetime import datetime
import os

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# 페이지 설정
st.set_page_config(
    page_title="마라톤 코칭 시스템",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화
if 'user' not in st.session_state:
    st.session_state.user = None

# 로그인 체크
if not st.session_state.user:
    st.switch_page("pages/login.py")

# 사이드바 설정
with st.sidebar:
    st.title("👤 사용자 정보")
    st.write(f"이름: {st.session_state.user['username']}")
    st.write(f"이메일: {st.session_state.user['email']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("회원 계정 관리"):
            st.switch_page("pages/account.py")
    with col2:
        if st.button("로그아웃"):
            st.session_state.user = None
            st.rerun()
            
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

#활동 누적 요약
def get_activity_summary():
    try:
        response = requests.get(
            f"{API_BASE_URL}/activities/summary/user/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return None

def format_duration(duration_str):
    # "HH:MM:SS" 형식의 문자열을 파싱
    try:
        hours, minutes, seconds = map(int, duration_str.split(':'))
        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초"
    except:
        return duration_str

# 탭 생성
tab1, tab5 = st.tabs(["홈", "활동 기록"])

# 홈 페이지
with tab1:
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

# 활동 기록 페이지
with tab5:
    st.title("🏃 활동 기록")

    # 활동 누적 요약 표시
    activity_summary = get_activity_summary()
    if activity_summary:
        st.subheader(f"Total {activity_summary['total_distance']} km")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.write(f"시간 : {format_duration(activity_summary['total_duration'])}")
        with col2:
            st.write("")
        with col3:
            st.write(f"평균 페이스 : {activity_summary['average_pace']}")
        with col4:
            st.write("")
        with col5:
            st.write(f"러닝 : {activity_summary['total_activities']}")
    else:
        st.info("활동 기록이 없습니다.")

    st.write("---")
    st.write("#### 활동 기록 목록")
    # 활동 기록 목록 표시
    activities = get_activities_laps()
    if activities:
        for activity in activities:
            # 날짜 형식 변환
            activity_date = datetime.fromisoformat(activity['local_start_time'].replace('Z', '+00:00'))
            formatted_date = activity_date.strftime('%Y년 %m월 %d일 - %H시 %M분')
            
            # 활동명을 25자로 고정하고 남는 공간을 특수 공백문자로 채움
            padded_activity_name = f"⠀⠀⠀##{activity['activity_name']}{'⠀' * (40 - len(activity['activity_name']))}"
            
            with st.expander(f"[{formatted_date}] {padded_activity_name} ({activity['distance']}km | {activity['duration']})"):
                st.write(f"#### {activity['activity_name']} - {formatted_date}")
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
                
                # 활동에 대한 댓글 입력
                st.write("---")
                st.write("💬 댓글을 남겨보세요")
                user_comment = st.text_area("", placeholder="이 활동에 대한 생각을 공유해보세요...", key=f"comment_{activity['activity_id']}")
                
                # 댓글 제출 버튼
                if st.button("댓글 작성", key=f"submit_comment_{activity['activity_id']}"):
                    if user_comment:
                        # TODO: 실제 API 엔드포인트로 변경 필요
                        # response = requests.post(
                        #     f"{API_BASE_URL}/activities/{activity['activity_id']}/comment",
                        #     headers={"Authorization": f"Bearer {st.session_state.token}"},
                        #     json={"comment": user_comment}
                        # )
                        # if response.status_code == 200:
                        #     st.success("댓글이 성공적으로 저장되었습니다.")
                        # else:
                        #     st.error("댓글 저장에 실패했습니다.")
                        st.success("댓글이 성공적으로 저장되었습니다.")  # 임시 성공 메시지
                    else:
                        st.warning("댓글을 입력해주세요.")

                # 피드백 버튼
                if st.button("활동 피드백 요청", key=f"feedback_{activity['activity_id']}"):
                    print("피드백 요청")
                    # TODO: 피드백 요청 API 호출  
                    # response = requests.post(
                    #     f"{API_BASE_URL}/activities/feedback/{activity['activity_id']}",
                    #     headers={"Authorization": f"Bearer {st.session_state.token}"}
                    # )
                    # if response.status_code == 200:
                    #     st.success("피드백 요청이 완료되었습니다.")
                    # else:
                    #     st.error("피드백 요청에 실패했습니다.")
    else:
        st.info("등록된 활동 기록이 없습니다.") 