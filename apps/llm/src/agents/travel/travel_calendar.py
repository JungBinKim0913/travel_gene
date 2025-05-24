from datetime import datetime, timedelta
import re
from typing import Dict, Optional, Tuple
from ...utils.calendar_service import get_calendar_service, create_calendar_event

DEFAULT_TRAVEL_DAYS = 3

DATE_PATTERN = r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
PERIOD_PATTERN = r'기간[:\s]*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?부터\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
DESTINATION_PATTERN = r'목적지[:\s]*([\w\s]+)'
OVERVIEW_PATTERN = r'주요 일정 개요[:\s]*(.*?)(?=\n|$)'

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

def create_travel_event_summary(destination: str, plan_content: str) -> str:
    """여행 이벤트 요약 생성"""
    summary = f"{destination} 여행"
    overview_match = re.search(OVERVIEW_PATTERN, plan_content)
    if overview_match:
        summary = f"{destination} - {overview_match.group(1).strip()}"
    return summary

def extract_travel_info(plan_data: Dict) -> Dict:
    """여행 계획에서 기본 정보 추출"""
    plan_content = plan_data.get("content", "")
    
    destination = extract_destination(plan_content)
    start_date, end_date = parse_travel_dates(plan_content)
    summary = create_travel_event_summary(destination, plan_content)
    
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary,
        "description": plan_content
    }

def create_travel_calendar_events(plan_data: Dict) -> Dict:
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
        
        result = create_calendar_event(
            service=service,
            summary=travel_info["summary"],
            start_date=travel_info["start_date"],
            end_date=travel_info["end_date"],
            description=travel_info["description"],
            location=travel_info["destination"]
        )
        
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