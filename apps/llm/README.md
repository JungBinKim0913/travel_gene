# Travel Gene LLM Service

여행 계획 생성을 위한 LLM 서비스입니다.

## 기능
- 여행 장소 검색 및 추천
- 여행 계획 생성
- 대화형 인터페이스

## 기술 스택
- FastAPI
- LangGraph
- LangChain

## 설치 방법
```bash
pip install -r requirements.txt
```

## 실행 방법
```bash
uvicorn src.main:app --reload
```

## API 문서
서버 실행 후 아래 URL에서 확인 가능:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
