import streamlit as st
import requests
from datetime import datetime, timedelta
import os
from components.activity_calendar import create_activity_calendar
from streamlit_calendar import calendar

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
if 'token' not in st.session_state:
    st.session_state.token = None

# 로그인 체크
if not st.session_state.user:
    st.switch_page("pages/login.py")

# 사이드바 설정
with st.sidebar:
    st.title("👤 사용자 정보")
    if st.session_state.user:
        st.write(f"이름: {st.session_state.user['username']}")
        st.write(f"이메일: {st.session_state.user['email']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("회원 계정 관리"):
                st.switch_page("pages/account.py")
        with col2:
            if st.button("로그아웃"):
                st.session_state.user = None
                st.session_state.token = None
                st.rerun()
    else:
        st.warning("로그인이 필요합니다.")
        if st.button("로그인"):
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

def get_dashboard_data():
    response = None

    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/user/{st.session_state.user['id']}",
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
tab1, tab5, tab6 = st.tabs(["홈", "활동 기록", "일정 관리"])

# 홈 페이지
with tab1:
    st.title(f"🏃 {st.session_state.user['username']}님, 환영합니다!")

    dashboard_data = get_dashboard_data()
    
    col1, col2 = st.columns(2)
    with col1:
    # 최근 활동 피드백 섹션
        with st.container():
            st.markdown("""
                <style>
                .recent-activity {
                    background-color: #f0f2f6;
                    padding: 10px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                </style>
                <div class="recent-activity">
                    <h4>📊 최근 활동 피드백</h4>
                </div>
            """, unsafe_allow_html=True)
            # TODO: 최근 활동 피드백 내용 추가
            if dashboard_data:
                st.write(dashboard_data['latest_feedback'])
            else:
                st.write("활동기록 탭에서 활동에 대한 피드백을 요청해주세요")
    
    with col2:
        # 장단점 피드백 섹션
        with st.container():
            st.markdown("""
                <style>
                .strength-weakness {
                    background-color: #e6f3ff;
                    padding: 10px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                </style>
                <div class="strength-weakness">
                    <h4>💪 나의 장단점 피드백</h4>
                </div>
            """, unsafe_allow_html=True)
            # TODO: 장단점 피드백 내용 추가
            if dashboard_data:
                st.write(dashboard_data['runner_feedback'])
            else:
                st.write("피드백 요청 탭에서 피드백을 요청해주세요")
    

    st.write("---")

    # 활동 캘린더 추가
    st.write("#### 활동 캘린더")
    activities = get_activities_laps()
    if activities:
        create_activity_calendar(activities)
    else:
        st.info("활동 기록이 없습니다.")

    st.write("---")

    # 내 정보 섹션
    with st.container():
        st.markdown("""
            <style>
            .user-info {
                background-color: #f0f7ff;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            </style>
            <div class="user-info">
                <h4>👤 내 정보</h4>
            </div>
        """, unsafe_allow_html=True)
        
        # 사용자 정보 표시
        user_data = get_user_data()
        if user_data:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"⠀⠀⠀이름: {user_data['username']}")
                st.write(f"⠀⠀⠀이메일: {user_data['email']}")
                st.write(f"⠀⠀⠀나이: {user_data['age']}세")
            with col2:
                st.write(f"체중: {user_data['weight']}kg")
                st.write(f"키: {user_data['height']}cm")
                st.write(f"목표 대회: {user_data['target_race']}")
                st.write(f"목표 시간: {user_data['target_time']}")

# 활동 기록 페이지
with tab5:
    activities = get_activities_laps()
    activity_summary = get_activity_summary()

    st.title("🏃 활동 기록")

    # 활동 누적 요약 표시
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


    # 수동 활동 등록 섹션
    with st.expander("➕ 새로운 활동 수동 등록하기"):
        st.subheader("활동 정보 입력")
        with st.form(key="activity_form"):
            activity_name = st.text_input("활동명", key="activity_name")
            col1, col2 = st.columns(2)
            with col1:
                distance = st.number_input("거리 (km)", min_value=0.1, step=0.1, key="distance")
                duration = st.text_input("소요 시간 (예: 01:30:00)", key="duration", help="HH:MM:SS 형식으로 입력해주세요")
                average_pace = st.text_input("평균 페이스 (예: 05:30)", key="average_pace", help="MM:SS 형식으로 입력해주세요")
            with col2:
                average_hr = st.number_input("평균 심박수 (bpm)", min_value=0, key="average_hr")
                max_hr = st.number_input("최대 심박수 (bpm)", min_value=0, key="max_hr")
                average_cadence = st.number_input("평균 케이던스 (spm)", min_value=0, key="average_cadence")
            
            submit_button = st.form_submit_button("활동 등록")
            
            if submit_button:
                if not all([activity_name, distance, duration, average_pace]):
                    st.error("필수 정보를 모두 입력해주세요.")
                else:
                    try:
                        # 시간 형식 검증
                        try:
                            hours, minutes, seconds = map(int, duration.split(':'))
                            duration_seconds = hours * 3600 + minutes * 60 + seconds
                        except:
                            st.error("소요 시간은 HH:MM:SS 형식으로 입력해주세요.")
                            st.stop()
                            
                        # 페이스 형식 검증
                        try:
                            pace_minutes, pace_seconds = map(int, average_pace.split(':'))
                            pace_seconds_total = pace_minutes * 60 + pace_seconds
                        except:
                            st.error("평균 페이스는 MM:SS 형식으로 입력해주세요.")
                            st.stop()
                        
                        activity_data = {
                            "activity_name": activity_name,
                            "distance": distance,
                            "duration": duration_seconds,
                            "average_pace": average_pace,
                            "average_hr": average_hr,
                            "max_hr": max_hr,
                            "average_cadence": average_cadence,
                            "start_time_local": datetime.now().isoformat(),
                            "activity_type": "running"
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}/activities/user/{st.session_state.user['id']}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            json=activity_data
                        )
                        
                        if response.status_code == 200:
                            st.success("활동이 성공적으로 등록되었습니다.")
                            st.rerun()
                        else:
                            st.error("활동 등록에 실패했습니다.")
                    except Exception as e:
                        st.error(f"활동 등록 중 오류가 발생했습니다: {str(e)}")

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
                st.write("💬 자신의 활동에 댓글을 남겨보세요(AI에게 핑계를 전달할 수 있어요)")
                
                # 기존 댓글들 표시
                if activity['comments']:
                    st.markdown("""
                        <style>
                        .comment-box {
                            background-color: #f0f2f6;
                            padding: 10px;
                            border-radius: 5px;
                            margin: 5px 0;
                            border-left: 3px solid #4CAF50;
                            position: relative;
                        }
                        .delete-button {
                            position: absolute;
                            top: 5px;
                            right: 5px;
                            color: #ff4444;
                            cursor: pointer;
                            font-size: 0.8em;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    for comment in activity['comments']:
                        col1, col2 = st.columns([0.95, 0.05])
                        with col1:
                            st.markdown(f"""
                                <div class="comment-box">
                                    <div style="color: #666; font-size: 0.8em;">{comment['created_at']}</div>
                                    <div style="margin-top: 5px;">{comment['comment']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_comment_{comment['id']}"):
                                try:
                                    response = requests.delete(
                                        f"{API_BASE_URL}/activities/comments/{comment['id']}",
                                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                                    )
                                    if response.status_code == 200:
                                        st.success("댓글이 삭제되었습니다.")
                                        st.rerun()
                                    else:
                                        st.error("댓글 삭제에 실패했습니다.")
                                except Exception as e:
                                    st.error(f"댓글 삭제 중 오류가 발생했습니다: {str(e)}")
                
                # 새 댓글 입력
                user_comment = st.text_area("", placeholder="이 활동에 대한 생각을 공유해보세요...", key=f"comment_{activity['activity_id']}")
                
                # 댓글 제출 버튼
                if st.button("댓글 작성", key=f"submit_comment_{activity['activity_id']}"):
                    if user_comment:
                        response = requests.post(
                            f"{API_BASE_URL}/activities/comments/",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            json={"activity_id": activity['activity_id'], "comment": user_comment}
                        )
                        if response.status_code == 200:
                            st.success("댓글이 성공적으로 저장되었습니다.")
                            st.rerun()  # 화면 새로고침
                        else:
                            st.error("댓글 저장에 실패했습니다.")
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

    # 가민에서 활동 기록 가져오기 버튼
    if st.button("가민에서 활동 기록 가져오기"):
        print("가민에서 활동 기록 가져오기")
        # TODO: 가민에서 활동 기록 가져오기 API 호출
        garmin_email = st.session_state.garmin_email    
        garmin_password = st.session_state.garmin_password
        response = requests.post(
            f"{API_BASE_URL}/sync-garmin-activities/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            json={"garmin_email": garmin_email, "garmin_password": garmin_password}
        )
        if response.status_code == 200:
            st.success("가민에서 활동 기록 가져오기 완료")
            st.rerun()
        else:
            st.error("가민에서 활동 기록 가져오기 실패")
    

# 일정 관리 페이지
with tab6:
    st.title("📅 일정 관리")
    
    # 일정 추가 폼
    with st.expander("➕ 새로운 일정 추가하기"):
        with st.form(key="schedule_form"):
            event_title = st.text_input("일정 제목")
            event_date = st.date_input("날짜")
            event_time = st.time_input("시간")
            event_description = st.text_area("설명")
            event_type = st.selectbox("일정 유형", ["훈련", "대회", "휴식", "기타"])
            
            # 일정 유형에 따른 색상 매핑
            color_mapping = {
                "훈련": "#4CAF50",  # 초록색
                "대회": "#FF5722",  # 주황색
                "휴식": "#2196F3",  # 파란색
                "기타": "#9C27B0"   # 보라색
            }
            
            submit_button = st.form_submit_button("일정 추가")
            
            if submit_button:
                if not event_title:
                    st.error("일정 제목을 입력해주세요.")
                else:
                    try:
                        event_datetime = datetime.combine(event_date, event_time)
                        event_data = {
                            "title": event_title,
                            "datetime": event_datetime.isoformat(),
                            "description": event_description,
                            "type": event_type,
                            "user_id": st.session_state.user['id']
                        }
                        
                        # 임시로 성공 메시지만 표시
                        st.success("일정이 성공적으로 추가되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"일정 추가 중 오류가 발생했습니다: {str(e)}")
    
    # 달력 뷰와 리스트 뷰를 탭으로 구분
    calendar_tab, list_tab = st.tabs(["📅 달력 보기", "📋 목록 보기"])
    
    # 임시 하드코딩된 일정 데이터
    mock_schedules = [
        {
            "id": 1,
            "title": "기초 체력 훈련",
            "datetime": datetime.now().replace(hour=9, minute=0).isoformat(),
            "description": "30분 러닝 + 스트레칭",
            "type": "훈련"
        },
        {
            "id": 2,
            "title": "서울 마라톤",
            "datetime": (datetime.now() + timedelta(days=7)).replace(hour=8, minute=0).isoformat(),
            "description": "2024 서울 마라톤 대회",
            "type": "대회"
        },
        {
            "id": 3,
            "title": "휴식일",
            "datetime": (datetime.now() + timedelta(days=2)).replace(hour=0, minute=0).isoformat(),
            "description": "완전 휴식",
            "type": "휴식"
        },
        {
            "id": 4,
            "title": "영양사 상담",
            "datetime": (datetime.now() + timedelta(days=3)).replace(hour=14, minute=30).isoformat(),
            "description": "마라톤 대비 영양 상담",
            "type": "기타"
        },
        {
            "id": 5,
            "title": "인터벌 훈련",
            "datetime": (datetime.now() + timedelta(days=1)).replace(hour=18, minute=0).isoformat(),
            "description": "400m x 10세트 인터벌 훈련",
            "type": "훈련"
        }
    ]
    
    # 달력 뷰
    with calendar_tab:
        # 일정 데이터를 달력 형식으로 변환
        calendar_events = []
        for schedule in mock_schedules:
            event_datetime = datetime.fromisoformat(schedule['datetime'])
            calendar_events.append({
                "title": schedule['title'],
                "start": event_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": (event_datetime + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "backgroundColor": color_mapping.get(schedule['type'], "#9C27B0"),
                "borderColor": color_mapping.get(schedule['type'], "#9C27B0"),
                "textColor": "#ffffff",
                "description": schedule['description'],
                "id": str(schedule['id'])
            })
        
        # 달력 표시
        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            "initialView": "dayGridMonth",
            "locale": "ko",
            "height": "600px",
            "editable": True,
            "selectable": True,
            "selectMirror": True,
            "dayMaxEvents": True,
            "weekends": True,
            "nowIndicator": True,
            "allDaySlot": True,
            "slotMinTime": "00:00:00",
            "slotMaxTime": "24:00:00"
        }
        
        calendar_result = calendar(
            events=calendar_events,
            options=calendar_options,
            key="calendar"
        )
        
        # 달력 이벤트 처리
        if calendar_result:
            st.write("선택된 일정:", calendar_result)
    
    # 리스트 뷰
    with list_tab:
        st.subheader("일정 목록")
        for schedule in mock_schedules:
            event_datetime = datetime.fromisoformat(schedule['datetime'])
            formatted_datetime = event_datetime.strftime('%Y년 %m월 %d일 - %H시 %M분')
            
            with st.expander(f"[{formatted_datetime}] {schedule['title']}"):
                st.write(f"**일정 유형:** {schedule['type']}")
                st.write(f"**설명:** {schedule['description']}")
                
                # 일정 삭제 버튼
                if st.button("🗑️ 삭제", key=f"delete_schedule_{schedule['id']}"):
                    st.success("일정이 삭제되었습니다.")
                    st.rerun()

    
