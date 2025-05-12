import streamlit as st
import requests
import os

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# 페이지 설정
st.set_page_config(
    page_title="회원 계정 관리",
    page_icon="👤",
    layout="wide"
)

# 로그인 체크
if not st.session_state.user:
    st.switch_page("pages/login.py")

st.title("회원 계정 관리")

# 사용자 정보 가져오기
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

# 사용자 정보 업데이트
def update_user_data(user_data):
    try:
        response = requests.put(
            f"{API_BASE_URL}/users/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            json=user_data
        )
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
    return False

def update_garmin_sync(user_data):
    try:
        response = requests.post(
            f"{API_BASE_URL}/users/garmin/{st.session_state.user['id']}",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            json=user_data
        )   
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
        return None

# 현재 사용자 정보 가져오기
user_data = get_user_data()

if user_data:
    st.subheader("회원 정보 수정")
    
    with st.form(key="edit_profile_form"):
        # 입력 필드 생성
        username = st.text_input("이름", value=user_data['username'])
        email = st.text_input("이메일", value=user_data['email'])
        age = st.number_input("나이", min_value=1, max_value=100, value=user_data['age'])
        weight = st.number_input("체중 (kg)", min_value=30.0, max_value=200.0, value=float(user_data['weight']))
        height = st.number_input("키 (cm)", min_value=100.0, max_value=250.0, value=float(user_data['height']))
        target_race = st.text_input("목표 대회", value=user_data['target_race'])
        target_time = st.text_input("목표 시간", value=user_data['target_time'])
        
        # 비밀번호 변경 (선택사항)
        st.subheader("비밀번호 변경 (선택사항)")
        current_password = st.text_input("현재 비밀번호", type="password")
        new_password = st.text_input("새 비밀번호", type="password")
        confirm_password = st.text_input("새 비밀번호 확인", type="password")
        
        # Submit button must be the last element in the form
        submit_button = st.form_submit_button(label="정보 수정")
        
        if submit_button:
            # 비밀번호 변경 확인
            if new_password:
                if new_password != confirm_password:
                    st.error("새 비밀번호가 일치하지 않습니다.")
                    st.stop()
                if not current_password:
                    st.error("현재 비밀번호를 입력해주세요.")
                    st.stop()
            
            # 업데이트할 데이터 준비
            update_data = {
                "username": username,
                "email": email,
                "age": age,
                "weight": weight,
                "height": height,
                "target_race": target_race,
                "target_time": target_time
            }
            
            # 비밀번호 변경이 있는 경우 추가
            if new_password:
                update_data.update({
                    "current_password": current_password,
                    "new_password": new_password
                })
            
            # 데이터 업데이트
            if update_user_data(update_data):
                st.success("회원 정보가 성공적으로 수정되었습니다.")
                st.rerun()
            else:
                st.error("회원 정보 수정에 실패했습니다.") 

    st.subheader("가민 연동")
    with st.form(key="edit_garmin_sync_form"):
        if user_data['garmin_sync_status'] == "success":
            garmin_email = user_data['garmin_email']
            st.success("가민 연동 정보가 성공적으로 연동되었습니다.")
            st.write(f"가민 이메일: {garmin_email}")
            disconnect_button = st.form_submit_button(label="가민 연동 해제")
            
            if disconnect_button:
                update_data = {
                    "garmin_sync_status": "disconnected"
                }
                response = update_garmin_sync(update_data)
                if response and response.get("garmin_sync_status") == "disconnected":
                    st.success("가민 연동 정보가 성공적으로 해제되었습니다.")
                    st.rerun()
                else:
                    st.error("가민 연동 해제에 실패했습니다.")
        else:
            garmin_email = st.text_input("가민 이메일", value=user_data['garmin_email'])
            garmin_password = st.text_input("가민 비밀번호", type="password")
            connect_button = st.form_submit_button(label="가민 연동")

            if connect_button:
                if garmin_email and garmin_password:
                    update_data = {
                        "garmin_email": garmin_email,
                        "garmin_password": garmin_password
                    }

                    try:
                        # 가민 연동 정보 수정
                        response = update_garmin_sync(update_data)
                        if response and response.get("garmin_sync_status") == "success":
                            st.success("가민 연동 정보가 성공적으로 등록되었습니다.")
                            st.session_state.garmin_email = garmin_email
                            st.session_state.garmin_password = garmin_password
                            st.rerun()
                        else:
                            error_message = response.get("detail", "가민 연동 정보 수정에 실패했습니다.")
                            st.error(f"가민 연동 정보 수정에 실패했습니다: {error_message}")
                    except Exception as e:
                        st.error(f"가민 연동 정보 수정 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.error("가민 이메일과 비밀번호를 모두 입력해주세요.")
