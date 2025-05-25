from datetime import datetime, timedelta
import os
from typing import Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']
REMINDER_TIME_MINUTES = 24 * 60
MAX_DESCRIPTION_LENGTH = 1000

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

def get_calendar_events(
    service,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    max_results: int = 50,
    query: Optional[str] = None
) -> Dict:
    """캘린더 이벤트 조회"""
    try:
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=30)
        
        time_min = start_date.isoformat() + 'Z'
        time_max = end_date.isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime',
            q=query
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', '제목 없음'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start': start,
                'end': end,
                'html_link': event.get('htmlLink', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', '')
            })
        
        return {
            "success": True,
            "events": formatted_events,
            "total_count": len(formatted_events)
        }
        
    except Exception as e:
        print(f"이벤트 조회 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "events": [],
            "total_count": 0
        }

def get_upcoming_events(service, days_ahead: int = 7) -> Dict:
    """다가오는 이벤트 조회"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days_ahead)
    
    return get_calendar_events(service, start_date, end_date)

def search_events_by_keyword(service, keyword: str, days_range: int = 365) -> Dict:
    """키워드로 이벤트 검색"""
    start_date = datetime.now() - timedelta(days=days_range//2)
    end_date = datetime.now() + timedelta(days=days_range//2)
    
    return get_calendar_events(service, start_date, end_date, query=keyword)

def get_event_by_id(service, event_id: str) -> Dict:
    """이벤트 ID로 특정 이벤트 조회"""
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        return {
            "success": True,
            "event": {
                'id': event['id'],
                'summary': event.get('summary', '제목 없음'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start': start,
                'end': end,
                'html_link': event.get('htmlLink', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', '')
            }
        }
    except Exception as e:
        print(f"이벤트 조회 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "event": {}
        }

def update_calendar_event(
    service,
    event_id: str,
    summary: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: str = 'Asia/Seoul'
) -> Dict:
    """캘린더 이벤트 수정"""
    try:
        existing_event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if summary is not None:
            existing_event['summary'] = summary
        if description is not None:
            existing_event['description'] = truncate_description(description)
        if location is not None:
            existing_event['location'] = location
        
        if start_date is not None:
            existing_event['start'] = {
                'date': start_date.strftime('%Y-%m-%d'),
                'timeZone': timezone,
            }
        
        if end_date is not None:
            existing_event['end'] = {
                'date': (end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'timeZone': timezone,
            }
        
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=existing_event
        ).execute()
        
        return {
            "success": True,
            "message": "이벤트가 성공적으로 수정되었습니다.",
            "event_link": updated_event.get('htmlLink'),
            "event_id": event_id
        }
        
    except Exception as e:
        print(f"이벤트 수정 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"이벤트 수정 중 오류가 발생했습니다: {str(e)}"
        }

def delete_calendar_event(service, event_id: str) -> Dict:
    """캘린더 이벤트 삭제"""
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        
        return {
            "success": True,
            "message": "이벤트가 성공적으로 삭제되었습니다.",
            "event_id": event_id
        }
        
    except Exception as e:
        print(f"이벤트 삭제 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"이벤트 삭제 중 오류가 발생했습니다: {str(e)}"
        } 