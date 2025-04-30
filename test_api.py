import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_user_creation():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "age": 30,
        "weight": 70.5,
        "height": 175.0,
        "target_race": "서울마라톤",
        "target_time": "3:30:00"
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    print("사용자 생성 응답:", response.json())
    return response.json()["id"]

def test_training_log(user_id):
    log_data = {
        "user_id": user_id,
        "date": datetime.now().isoformat(),
        "distance": 10.0,
        "duration": 60.0,
        "pace": 6.0,
        "heart_rate": 150.0,
        "notes": "쉬운 러닝"
    }
    response = requests.post(f"{BASE_URL}/training-logs/", json=log_data)
    print("훈련 로그 생성 응답:", response.json())

def test_sleep_log(user_id):
    log_data = {
        "user_id": user_id,
        "date": datetime.now().isoformat(),
        "duration": 7.5,
        "quality": 4,
        "notes": "잘 잤음"
    }
    response = requests.post(f"{BASE_URL}/sleep-logs/", json=log_data)
    print("수면 로그 생성 응답:", response.json())

def test_coaching_request(user_id):
    response = requests.post(f"{BASE_URL}/request-coaching/{user_id}")
    print("코칭 요청 응답:", response.json())
    return response.json()["feedback_id"]

def test_feedback(feedback_id):
    response = requests.get(f"{BASE_URL}/feedback/{feedback_id}")
    print("피드백 조회 응답:", response.json())

def run_all_tests():
    print("=== API 테스트 시작 ===")
    
    # 사용자 생성
    user_id = test_user_creation()
    
    # 훈련 로그 추가
    test_training_log(user_id)
    
    # 수면 로그 추가
    test_sleep_log(user_id)
    
    # AI 코칭 요청
    feedback_id = test_coaching_request(user_id)
    
    # 피드백 조회
    test_feedback(feedback_id)
    
    print("=== API 테스트 완료 ===")

if __name__ == "__main__":
    run_all_tests() 