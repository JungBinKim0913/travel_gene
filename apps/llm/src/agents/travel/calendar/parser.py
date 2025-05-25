from datetime import datetime, timedelta
import re
from typing import Dict, Optional, Tuple

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
    # JSON 형식 계획 처리
    if plan_data.get("plan_data"):
        json_plan = plan_data["plan_data"]
        
        # travel_overview에서 기본 정보 추출
        if "travel_overview" in json_plan:
            overview = json_plan["travel_overview"]
            destination = overview.get("destination", "여행")
            
            # 날짜 정보 추출
            start_date_str = overview.get("start_date")
            end_date_str = overview.get("end_date")
            
            start_date = None
            end_date = None
            
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                except ValueError:
                    pass
            
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                except ValueError:
                    pass
            
            # 기본값 설정
            if not start_date:
                start_date = datetime.now()
            if not end_date:
                end_date = start_date + timedelta(days=DEFAULT_TRAVEL_DAYS)
            
            summary = overview.get("summary", f"{destination} 여행")
            
            return {
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "summary": summary,
                "description": summary
            }
    
    # 기존 텍스트 형식 계획 처리 (하위 호환성)
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

def extract_destination_from_summary(summary: str) -> str:
    """이벤트 제목에서 목적지 추출"""
    patterns = [
        r'(.+?)\s*여행',
        r'(.+?)\s*-\s*',
        r'(.+?)\s*trip',
        r'(.+?)\s*투어'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, summary, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return summary.split()[0] if summary.split() else "미상"

def classify_travel_type(summary: str, description: str) -> str:
    """여행 유형 분류"""
    content = f"{summary} {description}".lower()
    
    if any(keyword in content for keyword in ["해외", "국외", "international", "overseas"]):
        return "해외여행"
    elif any(keyword in content for keyword in ["국내", "domestic", "한국"]):
        return "국내여행"
    elif any(keyword in content for keyword in ["출장", "business", "회사"]):
        return "출장"
    elif any(keyword in content for keyword in ["휴가", "vacation", "휴식"]):
        return "휴가"
    else:
        return "일반여행" 