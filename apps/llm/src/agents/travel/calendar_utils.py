from datetime import datetime, timedelta
import re
import os
from typing import Dict, Optional, Tuple
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']
DEFAULT_TRAVEL_DAYS = 3
REMINDER_TIME_MINUTES = 24 * 60
MAX_DESCRIPTION_LENGTH = 1000

DATE_PATTERN = r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
PERIOD_PATTERN = r'기간[:\s]*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?부터\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
DESTINATION_PATTERN = r'목적지[:\s]*([\w\s]+)'
OVERVIEW_PATTERN = r'주요 일정 개요[:\s]*(.*?)(?=\n|$)'

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

def parse_travel_dates(plan_content: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """여행 계획에서 시작일과 종료일 추출"""
    start_date = None
    end_date = None
    
    period_match = re.search(PERIOD_PATTERN, plan_content)
    if period_match:
        start_year, start_month, start_day, end_year, end_month, end_day = map(int, period_match.groups())
        try:
            start_date = datetime(start_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
            return start_date, end_date
        except ValueError:
            pass
    
    date_matches = re.findall(DATE_PATTERN, plan_content)
    if date_matches and len(date_matches) >= 2:
        try:
            start_year, start_month, start_day = map(int, date_matches[0])
            end_year, end_month, end_day = map(int, date_matches[-1])
            start_date = datetime(start_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
            return start_date, end_date
        except ValueError:
            pass
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=DEFAULT_TRAVEL_DAYS)
    return start_date, end_date

def extract_destination(plan_content: str) -> str:
    """여행 계획에서 목적지 추출"""
    destination = "여행"
    destination_match = re.search(DESTINATION_PATTERN, plan_content)
    if destination_match:
        destination = destination_match.group(1).strip()
    return destination

def create_event_summary(destination: str, plan_content: str) -> str:
    """이벤트 요약 생성"""
    summary = f"{destination} 여행"
    overview_match = re.search(OVERVIEW_PATTERN, plan_content)
    if overview_match:
        summary = f"{destination} - {overview_match.group(1).strip()}"
    return summary

def truncate_description(description: str) -> str:
    """설명 텍스트 길이 제한"""
    return description[:MAX_DESCRIPTION_LENGTH] if len(description) > MAX_DESCRIPTION_LENGTH else description

def extract_travel_info(plan_data: Dict) -> Dict:
    """여행 계획에서 기본 정보 추출"""
    plan_content = plan_data.get("content", "")
    
    destination = extract_destination(plan_content)
    start_date, end_date = parse_travel_dates(plan_content)
    summary = create_event_summary(destination, plan_content)
    description = truncate_description(plan_content)
    
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary,
        "description": description
    }

def create_calendar_event(travel_info: Dict, service) -> Dict:
    """캘린더 이벤트 생성 및 등록"""
    try:
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
        
        result = create_calendar_event(travel_info, service)
        
        if result["success"]:
            return {
                "success": True,
                "message": "여행 일정이 Google Calendar에 등록되었습니다.",
                "events_count": 1,
                "event_links": [result["event_link"]]
            }
        else:
            return {
                "success": False,
                "message": f"이벤트 생성 중 오류 발생: {result.get('error', '알 수 없는 오류')}",
                "events_count": 0
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Calendar 등록 중 오류 발생: {str(e)}",
            "events_count": 0
        } 