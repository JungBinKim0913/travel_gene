# Travel Gene LLM Service

Travel Gene 애플리케이션의 LLM 백엔드 서비스입니다.

## 기능

- 대화형 여행 계획 생성
- 실시간 스트리밍 응답
- Google Calendar 연동
- 카카오 Map API를 통한 실제 장소 검색
- 사용자 선호도 기반 맞춤 추천

## 기술 스택
- FastAPI
- LangGraph
- LangChain

## 설치 및 실행

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경변수 설정:
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```bash
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CALENDAR_API_KEY=your_google_calendar_api_key_here
KAKAO_API_KEY=your_kakao_rest_api_key_here
```

### 카카오 API 키 발급 방법

1. [카카오 개발자 콘솔](https://developers.kakao.com/) 접속
2. 애플리케이션 추가하기
3. 앱 설정 > 플랫폼 설정에서 Web 플랫폼 추가
4. 앱 키 > REST API 키 복사하여 KAKAO_API_KEY에 설정

3. 서버 실행:
```bash
uvicorn src.main:app --reload
```

## API 엔드포인트

- `POST /travel/plan`: 스트리밍 여행 계획 생성
- `GET /health`: 헬스 체크

## API 문서
서버 실행 후 아래 URL에서 확인 가능:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
