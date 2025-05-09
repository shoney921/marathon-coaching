import streamlit as st
import requests
import os

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# 페이지 설정
st.set_page_config(
    page_title="마라톤 코칭 시스템 - 회원가입",
    page_icon="🏃",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def register_user(user_data):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=user_data
        )
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
        return False

def main():
    st.title("회원가입")
    
    with st.form("register_form"):
        username = st.text_input("사용자 이름")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        confirm_password = st.text_input("비밀번호 확인", type="password")
        age = st.number_input("나이", min_value=1, max_value=100)
        weight = st.number_input("체중 (kg)", min_value=0.0)
        height = st.number_input("키 (cm)", min_value=0.0)
        target_race = st.text_input("목표 대회")
        target_time = st.text_input("목표 시간 (HH:MM:SS)")
        
        submitted = st.form_submit_button("회원가입")
        
        if submitted:
            if password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
                return
                
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "age": age,
                "weight": weight,
                "height": height,
                "target_race": target_race,
                "target_time": target_time
            }
            
            if register_user(user_data):
                st.success("회원가입이 완료되었습니다! 로그인 페이지로 이동합니다.")
                st.switch_page("pages/login.py")
            else:
                st.error("회원가입에 실패했습니다. 다시 시도해주세요.")
    
    # 로그인 페이지로 돌아가기
    st.write("이미 계정이 있으신가요?")
    if st.button("로그인"):
        st.switch_page("login.py")

if __name__ == "__main__":
    main() 