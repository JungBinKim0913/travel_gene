# 🗺️ Travel Gene Client

AI와 함께하는 똑똑한 여행 계획 웹 애플리케이션

## 📋 개요

Travel Gene은 AI 기반 여행 계획 도우미로, 사용자와의 자연스러운 대화를 통해 맞춤형 여행 계획을 생성하고 Google Calendar와 연동하여 일정을 관리할 수 있는 Streamlit 웹 애플리케이션입니다.

## ✨ 주요 기능

### 💬 여행 채팅
- AI 여행 전문가와 실시간 대화
- 개인 맞춤형 여행 추천
- 실시간 일정 관리
- Google Calendar 연동

### 🌐 여행 공유
- 완성된 여행 계획 공유
- 모바일 최적화된 디자인
- 간편한 링크 공유 기능

## 🚀 빠른 시작

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

```bash
pip3 install -r requirements.txt
```

### 2. 애플리케이션 실행

```bash
cd apps/client

streamlit run app.py
```

애플리케이션이 성공적으로 실행되면 브라우저에서 `http://localhost:8501`로 접속할 수 있습니다.

## 📁 프로젝트 구조

```
apps/client/
├── app.py                 # 메인 애플리케이션 파일
├── requirements.txt       # Python 의존성
├── README.md             # 이 파일
├── pages/                # Streamlit 페이지들
│   ├── 1_chat.py         # 여행 채팅 페이지
│   └── 2_share.py        # 여행 공유 페이지
└── src/                  # 소스 코드
    ├── __init__.py
    ├── share/            # 공유 관련 모듈
    └── utils/            # 유틸리티 함수들
```


## 🔗 LLM 연동

이 클라이언트는 Travel Gene LLM 서버와 연동됩니다:

```bash
# LLM 서버 실행 (별도 터미널)
cd apps/llm
python -m uvicorn main:app --reload --port 8000
```

LLM이 실행되지 않은 경우, 일부 기능이 제한될 수 있습니다.
