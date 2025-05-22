from datetime import datetime, timedelta
import re
import os
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']

current_dir = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(current_dir, 'credentials.json')
TOKEN_FILE = os.path.join(current_dir, 'token.json')

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

def extract_travel_info(plan_data: Dict) -> Dict:
    """여행 계획에서 기본 정보만 추출"""
    plan_content = plan_data.get("content", "")
    
    destination = "여행"
    destination_match = re.search(r'목적지[:\s]*([\w\s]+)', plan_content)
    if destination_match:
        destination = destination_match.group(1).strip()
    
    start_date = None
    end_date = None
    
    period_match = re.search(r'기간[:\s]*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?부터\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', plan_content)
    if period_match:
        start_year, start_month, start_day, end_year, end_month, end_day = map(int, period_match.groups())
        start_date = datetime(start_year, start_month, start_day)
        end_date = datetime(end_year, end_month, end_day)
    else:
        date_matches = re.findall(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', plan_content)
        if date_matches and len(date_matches) >= 2:
            start_year, start_month, start_day = map(int, date_matches[0])
            end_year, end_month, end_day = map(int, date_matches[-1])
            start_date = datetime(start_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
    
    if not start_date:
        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)
    
    summary = f"{destination} 여행"
    overview_match = re.search(r'주요 일정 개요[:\s]*(.*?)(?=\n|$)', plan_content)
    if overview_match:
        summary = f"{destination} - {overview_match.group(1).strip()}"
    
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary,
        "description": plan_content[:1000] if len(plan_content) > 1000 else plan_content
    }

def create_calendar_events(plan_data: Dict) -> Dict:
    """여행 계획을 Google Calendar에 등록"""
    try:
        service = get_calendar_service()
        
        if not service:
            return {
                "success": False,
                "message": "Google Calendar 서비스 연결에 실패했습니다. credentials.json 파일을 확인해주세요.",
                "events_count": 0
            }
        
        travel_info = extract_travel_info(plan_data)
        
        event = {
            'summary': travel_info["summary"],
            'location': travel_info["destination"],
            'description': travel_info["description"],
            'start': {
                'date': travel_info["start_date"].strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'date': (travel_info["end_date"] + timedelta(days=1)).strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Seoul',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 24 * 60},
                ],
            },
        }
        
        created_event = service.events().insert(
            calendarId='primary', body=event).execute()
        
        return {
            "success": True,
            "message": f"여행 일정이 Google Calendar에 등록되었습니다.",
            "events_count": 1,
            "event_links": [created_event.get('htmlLink')]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Calendar 등록 중 오류 발생: {str(e)}",
            "events_count": 0
        } 