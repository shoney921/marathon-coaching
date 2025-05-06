import os
import time
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

        if not email or not password:
            raise ValueError("GARMIN_EMAIL 또는 GARMIN_PASSWORD 환경 변수가 설정되지 않았습니다.")

        client = Garmin(email, "password")
        
        # 로그인
        client.login()
        print("로그인 성공!")
        
        # 기본 정보 가져오기
        print("\n사용자 정보 조회...")
        print("사용자 이름:", client.get_full_name())
        
        # 최근 활동 가져오기
        # print("\n활동 데이터 조회 시도...")
        # try:
        #     activities = client.get_activities(0, 5)  # 최근 5개의 활동만 조회
        #     print(f"활동 데이터 응답: {activities}")
            
        #     if activities:
        #         for activity in activities:
        #             print("\n최근 활동:")
        #             print(f"활동명: {activity.get('activityName')}")
        #             print(f"거리: {activity.get('distance')} km")
        #             print(f"시간: {activity.get('duration')} 초")
        #             print(f"속도: {activity.get('speed')} km/h")
        #             print(f"칼로리: {activity.get('calories')} kcal")
        #             print(f"타임: {activity.get('time')} 초")
        #     else:
        #         print("활동 데이터가 없습니다.")
                
        # except Exception as activity_error:
        #     print(f"활동 데이터 조회 중 에러 발생: {str(activity_error)}")
            
    except Exception as e:
        print(f"전체 에러 발생: {str(e)}")

if __name__ == "__main__":
    get_garmin_data()        