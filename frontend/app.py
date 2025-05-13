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
if 'calendar_key' not in st.session_state:
    st.session_state.calendar_key = 0

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

def get_schedules():
    try:
        response = requests.get(
            f"{API_BASE_URL}/activities/training-schedule/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"응답 처리 오류: {response.status_code}")
            return []
        
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return []

def delete_schedule(schedule_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/activities/training-schedule/{st.session_state.user['id']}/{schedule_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"응답 처리 오류: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
        return None

# 탭 생성
tab1, tab5, tab6, tab7 = st.tabs(["🏠 홈", "📊 활동 기록", "📅 일정 관리", "🤖 러닝 코치"])

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
                st.write("💬 자신의 활동에 댓글을 남겨보세요(피드백 요청 전에 작성하면,AI에게 핑계를 전달할 수 있어요)")
                
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

                if activity['feedback']:
                    st.write("#### 활동 피드백")
                    st.write(f"{activity['feedback']}")
                else:
                    # 피드백 버튼
                    if st.button("활동 피드백 요청", key=f"feedback_{activity['activity_id']}"):
                        try:
                            comments = [comment['comment'] for comment in activity['comments']]
                            
                            response = requests.post(
                                f"{API_BASE_URL}/activities/feedback/{st.session_state.user['id']}/{activity['activity_id']}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                json={"comments": comments}
                            )
                            if response.status_code == 200:
                                feedback = response.json()
                                st.success("피드백이 생성되었습니다.")
                                st.rerun()
                            else:
                                st.error("피드백 요청에 실패했습니다.")
                        except Exception as e:
                            st.error(f"피드백 요청 중 오류가 발생했습니다: {str(e)}")
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
    
    # 일정 유형에 따른 색상 매핑
    color_mapping = {
        "훈련": "#4CAF50",  # 초록색
        "대회": "#FF5722",  # 주황색
        "휴식": "#2196F3",  # 파란색
        "기타": "#9C27B0"   # 보라색
    }
    
    # 실제 일정 데이터 가져오기
    schedules = get_schedules()
    
    # 달력 뷰와 리스트 뷰를 탭으로 구분
    calendar_tab, list_tab, agent_tab = st.tabs(["📅 달력 보기", "📋 목록 보기", "🤖일정 에이전트"])
    
    # 달력 뷰
    with calendar_tab:
        st.markdown("### 훈련 일정 캘린더")
        if st.button("🔄"):
            st.session_state.calendar_key += 1
            st.rerun()
        
        # 캘린더 이벤트 데이터 준비
        calendar_events = []
        if schedules:
            for schedule in schedules:
                try:
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
                except Exception as e:
                    st.error(f"일정 데이터 변환 중 오류 발생: {str(e)}")
                    continue
        
        # 달력 옵션 설정
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
        
        # 캘린더가 비어있을 때 메시지 표시
        if not calendar_events:
            st.info("표시할 일정이 없습니다. 새로운 일정을 생성해보세요!")
        else:
            # 세션 상태의 key를 사용하여 캘린더 렌더링
            calendar_result = calendar(
                events=calendar_events,
                options=calendar_options,
                key=f"calendar_{st.session_state.calendar_key}"
            )
            
            # 달력 이벤트 처리
            if calendar_result:
                # 선택된 일정 정보를 깔끔하게 표시
                with st.container():
                    if isinstance(calendar_result, dict) and 'eventClick' in calendar_result:
                        event = calendar_result['eventClick']['event']
                        st.subheader(f"📅 {event.get('title', '정보 없음')}")
                        col1, col2 = st.columns(2)
                        with col1:
                            # 시작 시간 포맷팅 (한국 시간대 고려)
                            start_time = event.get('start', '').replace('+09:00', '')
                            st.write("**시작 시간:**", start_time.replace('T', ' '))
                        with col2:
                            # 종료 시간 포맷팅 (한국 시간대 고려)
                            end_time = event.get('end', '').replace('+09:00', '')
                            st.write("**종료 시간:**", end_time.replace('T', ' '))
                        st.write("**설명:**")
                        st.write(event.get('extendedProps', {}).get('description', '정보 없음'))
                    else:
                        st.info("일정을 선택하면 상세 정보가 표시됩니다.")
                
    
    # 리스트 뷰
    with list_tab:
        st.subheader("일정 목록")

        # 일정 추가 폼
        with st.expander("➕ 새로운 일정 추가하기"):
            with st.form(key="schedule_form"):
                event_title = st.text_input("일정 제목")
                event_date = st.date_input("날짜")
                event_time = st.time_input("시간")
                event_description = st.text_area("설명")
                event_type = st.selectbox("일정 유형", ["훈련", "대회", "휴식", "기타"])
                
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

        for schedule in schedules:
            event_datetime = datetime.fromisoformat(schedule['datetime'])
            formatted_datetime = event_datetime.strftime('%Y년 %m월 %d일 - %H시 %M분')
            
            with st.expander(f"[{formatted_datetime}] {schedule['title']}"):
                st.write(f"**일정 유형:** {schedule['type']}")
                st.write(f"**설명:** {schedule['description']}")
                
                # 일정 삭제 버튼
                if st.button("🗑️ 삭제", key=f"delete_schedule_{schedule['id']}"):
                    response = delete_schedule(schedule['id'])
                    if response is not None:
                        st.success("일정이 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.error("일정 삭제에 실패했습니다.")

    # 일정 생성 에이전트
    with agent_tab:
        st.title("🤖 일정 에이전트")
        st.write("나의 러닝 활동 데이터를 참조하여 새로운 훈련 일정을 생성합니다.")
        # 목표 대회 정보 입력 폼
        with st.form("race_target_form"):
            st.subheader("🎯 목표 대회 정보")
            
            
            col1, col2 = st.columns(2)
            
            with col1:
                race_name = st.text_input("목표 대회명", placeholder="예: 서울 마라톤") 
                race_date = st.date_input(
                    "대회 날짜",
                    min_value=datetime.now().date(),
                    help="대회 날짜를 선택해주세요"
                )
            
            with col2:
                race_type = st.selectbox(
                    "대회 타입",
                    options=["풀 마라톤(42.195km)", "하프 마라톤(21.0975km)", "10K", "5K"],
                    format_func=lambda x: x.split("(")[0] if "(" in x else x
                )
                time_col1, time_col2, time_col3 = st.columns(3)
                with time_col1:
                    hours = st.number_input("목표 시간", min_value=0, max_value=23, value=4)
                with time_col2:
                    minutes = st.number_input("분", min_value=0, max_value=59, value=0)
                with time_col3:
                    seconds = st.number_input("초", min_value=0, max_value=59, value=0)
                
                target_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                race_date = race_date.strftime("%Y-%m-%d")

            # 특이사항 입력 필드 추가
            st.write("---")
            st.subheader("💭 특이사항 및 요청사항")
            special_notes = st.text_area(
                "특이사항이나 요청사항을 입력해주세요",
                placeholder="예: 부상 이력, 훈련 선호도, 특별히 고려해야 할 사항 등",
                help="훈련 일정 생성 시 고려해야 할 특이사항이나 요청사항을 자유롭게 입력해주세요",
                height=100
            )
            
            submit_button = st.form_submit_button("대회 일정 생성")
            
            if submit_button:
                if not race_name:
                    st.error("목표 대회명을 입력해주세요.")
                else:
                    st.success(f"""목표가 설정되었습니다!
                    - 대회명: {race_name}
                    - 대회 타입: {race_type}
                    - 목표 시간: {target_time}""")
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/activities/training-schedule/{st.session_state.user['id']}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            json={"race_name": race_name, "race_date": race_date, "race_type": race_type, "race_time": target_time, "special_notes": special_notes}
                        )
                        
                        if response.status_code == 200:
                            schedule_data = response.json()
                            st.success("훈련 일정 생성 완료")
                            st.rerun()
                        else:
                            error_detail = response.json().get('detail', '알 수 없는 오류가 발생했습니다.')
                            st.error(f"훈련 일정 생성 실패: {error_detail}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"서버 연결 오류: {str(e)}")
                    except ValueError as e:
                        st.error(f"응답 처리 오류: {str(e)}")

                
    

# 러닝 코치 페이지
with tab7:
    st.title("🤖 러닝 코치")
    st.write("러닝에 관한 질문을 자유롭게 해보세요!")

    # 대화 기록을 저장할 세션 상태 초기화
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # 채팅 인터페이스 스타일
    st.markdown("""
        <style>
        .chat-message {
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 20%;
        }
        .assistant-message {
            background-color: #f5f5f5;
            margin-right: 20%;
        }
        .message-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .message-header img {
            width: 24px;
            height: 24px;
            margin-right: 0.5rem;
        }
        .message-content {
            line-height: 1.5;
        }
        </style>
    """, unsafe_allow_html=True)

    # 채팅 기록 표시
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="message-header">
                        <img src="https://img.icons8.com/color/48/000000/user.png" alt="User"/>
                        <div style="font-weight: bold;">나</div>
                    </div>
                    <div class="message-content">{message["content"]}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div class="message-header">
                        <img src="https://img.icons8.com/color/48/000000/coach.png" alt="Coach"/>
                        <div style="font-weight: bold;">러닝 코치</div>
                    </div>
                    <div class="message-content">{message["content"]}</div>
                </div>
            """, unsafe_allow_html=True)

    # 사용자 입력
    user_input = st.text_area(
        "질문을 입력하세요",
        placeholder="예: 초보자가 시작할 때 적절한 페이스는 어떻게 되나요?",
        height=100
    )

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        if st.button("질문하기", use_container_width=True):
            if user_input:
                # 사용자 메시지 추가
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # 로딩 표시
                with st.spinner("러닝 코치가 답변을 준비중입니다..."):
                    # API 요청 데이터 준비
                    request_data = {
                        "user_message": user_input,
                        "chat_history": st.session_state.chat_history,
                        "user_id": st.session_state.user_id,  # 사용자 ID
                        "activities": st.session_state.activities,  # 사용자의 활동 데이터
                        "training_schedule": st.session_state.training_schedule  # 훈련 일정
                    }
                    
                    # API 호출
                    response = requests.post(
                        f"{API_BASE_URL}/running-coach/prompt",
                        json=request_data
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        response = response_data["message"]
                    else:
                        response = "죄송합니다. 답변을 생성하는 중에 문제가 발생했습니다."
                    
                    
                    # 어시스턴트 메시지 추가
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                # 화면 새로고침
                st.rerun()
            else:
                st.warning("질문을 입력해주세요.")
    
    with col2:
        if st.button("대화 초기화", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # 도움말 섹션
    with st.expander("💡 도움말"):
        st.markdown("""
        ### 질문 예시
        - 초보자가 시작할 때 적절한 페이스는 어떻게 되나요?
        - 러닝 중 호흡법은 어떻게 해야 하나요?
        - 장거리 러닝을 위한 영양 섭취 방법은?
        - 러닝 중 발생하는 통증을 예방하는 방법은?
        - 목표 시간을 달성하기 위한 훈련 계획은 어떻게 세워야 하나요?
        
        ### 팁
        - 구체적인 질문을 하면 더 정확한 답변을 받을 수 있습니다.
        - 현재 러닝 수준과 목표를 함께 언급하면 더 맞춤형 조언을 받을 수 있습니다.
        - 부상이나 건강 상태에 대한 질문은 전문의와 상담하시기 바랍니다.
        """)

    
    
