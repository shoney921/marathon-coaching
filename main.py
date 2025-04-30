import os
from dotenv import load_dotenv
from garminconnect import Garmin
from datetime import datetime, timedelta

# .env 파일에서 환경 변수 로드
load_dotenv()

def get_garmin_data():
    try:
        # Garmin Connect 클라이언트 초기화 (토큰은 ~/.garminconnect 디렉토리에 저장됨)
        email = os.getenv('GARMIN_EMAIL')
        password = os.getenv('GARMIN_PASSWORD')

        client = Garmin(email, password)
        
        # 로그인
        client.login()
        
        # 기본 정보 가져오기
        print("사용자 이름:", client.get_full_name())

        # 최근 5일간의 데이터 가져오기
        startDate = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        print("베터리 데이터:", client.get_body_battery(startDate))
        
        # 오늘 날짜의 데이터 가져오기
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 최근 활동 가져오기
        activities = client.get_activities(0, 5)  # 최근 5개의 활동
        if activities:
            for activity in activities:
                print("\n최근 활동:")
                print(f"활동명: {activity.get('activityName')}")
                print(f"거리: {activity.get('distance')} km")
                print(f"시간: {activity.get('duration')} 초")
                print(f"속도: {activity.get('speed')} km/h")
                print(f"칼로리: {activity.get('calories')} kcal")
                print(f"타임: {activity.get('time')} 초")
                print(activity)
            
        # 수면 데이터 가져오기
        sleep_data = client.get_sleep_data(today)
        if sleep_data:
            print("\n수면 데이터:")
            print(f"수면 시간: {sleep_data.get('sleepTimeSeconds', 0) / 3600:.2f} 시간")
            
    except Exception as e:
        print(f"에러 발생: {str(e)}")

if __name__ == "__main__":
    get_garmin_data()        