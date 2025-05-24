from datetime import datetime, timedelta
import os
from typing import Dict
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']
REMINDER_TIME_MINUTES = 24 * 60
MAX_DESCRIPTION_LENGTH = 1000

# credentials.json 파일을 프로젝트 루트에서 찾도록 수정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_FILE = os.path.join(PROJECT_ROOT, 'token.json')

def get_calendar_service():
    """Google Calendar API 서비스 객체 생성"""
    try:
        creds = None
        
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_info(
                info=eval(open(TOKEN_FILE).read()), scopes=SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(str(creds.to_json()))
        
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"캘린더 서비스 초기화 오류: {str(e)}")
        return None

def truncate_description(description: str) -> str:
    """설명 텍스트 길이 제한"""
    return description[:MAX_DESCRIPTION_LENGTH] if len(description) > MAX_DESCRIPTION_LENGTH else description

def create_calendar_event(
    service, 
    summary: str, 
    start_date: datetime, 
    end_date: datetime, 
    description: str = "", 
    location: str = "",
    timezone: str = 'Asia/Seoul'
) -> Dict:
    """캘린더 이벤트 생성 및 등록"""
    try:
        event = {
            'summary': summary,
            'location': location,
            'description': truncate_description(description),
            'start': {
                'date': start_date.strftime('%Y-%m-%d'),
                'timeZone': timezone,
            },
            'end': {
                'date': (end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'timeZone': timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': REMINDER_TIME_MINUTES},
                ],
            },
        }
        
        created_event = service.events().insert(
            calendarId='primary', body=event).execute()
        
        return {
            "success": True,
            "event_link": created_event.get('htmlLink')
        }
    except Exception as e:
        print(f"이벤트 생성 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 