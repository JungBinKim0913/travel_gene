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

def parse_date_from_plan(date_text: str) -> Optional[datetime]:
    """여행 계획에서 날짜 추출"""
    date_pattern = r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
    match = re.search(date_pattern, date_text)
    
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
    
    return None

def extract_events_from_plan(plan_data: Dict) -> List[Dict]:
    """여행 계획에서 일정 이벤트 추출"""
    events = []
    plan_content = plan_data.get("content", "")
    
    destination = None
    destination_match = re.search(r'목적지[:\s]*([\w\s]+)', plan_content)
    if destination_match:
        destination = destination_match.group(1).strip()
    
    day_sections = re.split(r'\n\s*\d+일차|\n\s*Day \d+', plan_content)
    
    if len(day_sections) <= 1:
        day_sections = re.findall(r'((?:\d{4}년)?\s*\d{1,2}월\s*\d{1,2}일.*?)(?=(?:\d{4}년)?\s*\d{1,2}월\s*\d{1,2}일|$)', plan_content, re.DOTALL)
    
    current_date = None
    
    for section in day_sections:
        date_match = re.search(r'((?:\d{4}년)?\s*\d{1,2}월\s*\d{1,2}일)', section)
        if date_match:
            date_text = date_match.group(1)
            parsed_date = parse_date_from_plan(date_text)
            
            if parsed_date:
                current_date = parsed_date
                
                activities = re.findall(r'(\d{1,2}:\d{2}(?:\s*[~-]\s*\d{1,2}:\d{2})?)[\s:]+([^\n]+)', section)
                
                for time_range, activity in activities:
                    start_time, end_time = None, None
                    
                    if '~' in time_range or '-' in time_range:
                        start_end = re.split(r'\s*[~-]\s*', time_range)
                        if len(start_end) == 2:
                            start_time, end_time = start_end
                    else:
                        start_time = time_range
                        hours, minutes = map(int, start_time.split(':'))
                        end_hours = hours + 1
                        end_time = f"{end_hours:02d}:{minutes:02d}"
                    
                    start_hour, start_minute = map(int, start_time.split(':'))
                    end_hour, end_minute = map(int, end_time.split(':'))
                    
                    event_start = current_date.replace(hour=start_hour, minute=start_minute)
                    event_end = current_date.replace(hour=end_hour, minute=end_minute)
                    
                    events.append({
                        'summary': activity.strip(),
                        'location': destination,
                        'start': {
                            'dateTime': event_start.isoformat(),
                            'timeZone': 'Asia/Seoul',
                        },
                        'end': {
                            'dateTime': event_end.isoformat(),
                            'timeZone': 'Asia/Seoul',
                        },
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'popup', 'minutes': 30},
                            ],
                        },
                    })
    
    return events

def create_calendar_events(plan_data: Dict) -> Dict:
    """여행 계획을 Google Calendar에 등록"""
    try:
        service = get_calendar_service()
        events = extract_events_from_plan(plan_data)
        
        if not events:
            return {
                "success": False,
                "message": "일정을 추출할 수 없습니다.",
                "events_count": 0
            }
        
        created_events = []
        for event in events:
            created_event = service.events().insert(
                calendarId='primary', body=event).execute()
            created_events.append(created_event.get('htmlLink'))
        
        return {
            "success": True,
            "message": f"{len(created_events)}개의 일정이 Google Calendar에 등록되었습니다.",
            "events_count": len(created_events),
            "event_links": created_events
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Calendar 등록 중 오류 발생: {str(e)}",
            "events_count": 0
        } 