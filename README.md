# Garmin Connect API 사용 가이드

이 프로젝트는 Garmin Connect API를 사용하여 데이터를 가져오는 Python 스크립트입니다.

## API 키 발급 방법

1. Garmin 개발자 포털 접속:

   - https://developer.garmin.com/garmin-connect-api/ 에 접속

2. 개발자 계정 생성:

   - "Sign Up" 또는 "Register" 버튼 클릭
   - 필요한 정보 입력 후 계정 생성

3. API 키 발급:
   - 로그인 후 "My Apps" 섹션으로 이동
   - "Create a new app" 클릭
   - 앱 정보 입력 (앱 이름, 설명, 웹사이트 URL 등)
   - OAuth 2.0 클라이언트 ID와 시크릿 발급

## 설치 방법

1. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
   - `.env` 파일을 프로젝트 루트 디렉토리에 생성
   - 다음 내용을 추가:
   ```
   GARMIN_CLIENT_ID=your_client_id_here
   GARMIN_CLIENT_SECRET=your_client_secret_here
   ```

## 사용 방법

1. `.env` 파일에 Garmin API 인증 정보를 입력
2. 다음 명령어로 스크립트 실행:

```bash
python main.py
```

3. 표시되는 URL로 이동하여 인증을 완료
4. 인증 코드를 입력

## 기능

- 오늘의 활동 데이터 조회
- 일일 통계 정보 조회 (걸음 수, 칼로리, 활동 시간 등)

## 주의사항

- Garmin 개발자 계정이 필요합니다
- API 키는 보안을 위해 `.env` 파일에 저장하세요
- `.env` 파일은 절대 git에 커밋하지 마세요
