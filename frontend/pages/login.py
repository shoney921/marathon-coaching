import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# API 엔드포인트 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# 페이지 설정
st.set_page_config(
    page_title="마라톤 코칭 시스템 - 로그인",
    page_icon="🏃",
    layout="centered"
)

def login_user(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            response_data = response.json()
            st.session_state.user = response_data['user']   
            st.session_state.token = response_data['token']
            st.success("로그인 성공!")
            st.rerun()
            return response_data['user']
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
        return None

def main():
    st.title("🏃 마라톤 코칭 시스템")
    
    # 세션 상태 초기화
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # 이미 로그인된 경우 메인 페이지로 리다이렉트
    if st.session_state.user:
        st.switch_page("app.py")
    
    # 로그인 폼
    with st.form("login_form"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")
        
        if submitted:
            user_data = login_user(email, password)
            if user_data:
                st.session_state.user = user_data
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
    
    # 회원가입 링크
    st.write("계정이 없으신가요?")
    if st.button("회원가입"):
        st.switch_page("pages/register.py")

if __name__ == "__main__":
    main() 