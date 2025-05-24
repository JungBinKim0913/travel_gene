from datetime import datetime, timedelta
import re
from typing import Dict, Optional, Tuple, List
from langchain_core.messages import HumanMessage
from ...utils.calendar_service import (
    get_calendar_service, 
    create_calendar_event,
    get_calendar_events,
    get_upcoming_events,
    search_events_by_keyword
)

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

def register_travel_calendar(plan_data: Dict) -> Dict:
    """여행 계획을 Google Calendar에 등록 (state handler용)"""
    return create_travel_calendar_events(plan_data)

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

def view_travel_calendar(messages: List, conversation_state: Dict) -> Dict:
    """Google Calendar에서 여행 일정 조회"""
    try:
        last_user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_message = msg.content.lower()
                break
        
        if last_user_message:
            if any(word in last_user_message for word in ["다가오는", "앞으로", "예정", "예정된"]):
                calendar_result = get_upcoming_travel_events(30)
                query_type = "다가오는 여행 일정"
            elif conversation_state.get("destination"):
                destination = conversation_state.get("destination")
                calendar_result = search_travel_by_destination(destination)
                query_type = f"{destination} 관련 여행 일정"
            else:
                calendar_result = get_travel_events()
                query_type = "전체 여행 일정"
        else:
            calendar_result = get_upcoming_travel_events(30)
            query_type = "다가오는 여행 일정"
        
        if calendar_result["success"]:
            events = calendar_result["events"]
            total_count = calendar_result["total_count"]
            
            if total_count > 0:
                event_list = []
                for i, event in enumerate(events, 1):
                    start_date = event.get("start", "").split("T")[0] if "T" in event.get("start", "") else event.get("start", "")
                    end_date = event.get("end", "").split("T")[0] if "T" in event.get("end", "") else event.get("end", "")
                    
                    event_lines = [
                        f"**{i}. {event.get('summary', '제목 없음')}**  ",
                        f"📅 **기간:** {start_date} ~ {end_date}  ",
                        f"📍 **장소:** {event.get('location', '장소 미정')}  "
                    ]
                    
                    if event.get('html_link'):
                        event_lines.append(f"🔗 **링크:** [Calendar에서 보기]({event.get('html_link')})  ")
                    
                    if event.get('description') and len(event['description']) > 0:
                        description = event['description'][:200] + "..." if len(event['description']) > 200 else event['description']
                        event_lines.append(f"📝 **설명:** {description}  ")
                    
                    event_list.append('\n'.join(event_lines))
                
                events_text = '\n\n---\n\n'.join(event_list)
                
                message = f"""{query_type} 조회 결과입니다:

**총 {total_count}개의 일정을 찾았습니다.**

{events_text}

---

모든 일정은 Calendar에서 자세히 확인하실 수 있습니다.  
특정 일정을 수정하거나 삭제하고 싶으시면 말씀해주세요."""
            else:
                message = f"""{query_type} 조회 결과, 등록된 일정이 없습니다.

새로운 여행 계획을 세워보시겠어요? 원하시는 여행지나 기간을 말씀해주시면 계획을 도와드리겠습니다."""
        else:
            message = f"""죄송합니다. Calendar 조회 중 문제가 발생했습니다.

오류 내용: {calendar_result.get('message', '알 수 없는 오류')}

Calendar 연결을 확인하거나 다시 시도해주세요."""
        
        return {
            "success": calendar_result["success"],
            "message": message,
            "calendar_data": calendar_result
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Calendar 조회 중 오류 발생: {str(e)}",
            "calendar_data": {}
        }

def get_travel_events() -> Dict:
    """여행 관련 이벤트 조회"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "success": False,
                "message": "Google Calendar 서비스 연결에 실패했습니다.",
                "events": [],
                "total_count": 0
            }
        
        result = search_events_by_keyword(service, "여행")
        
        if result["success"]:
            travel_events = []
            for event in result["events"]:
                travel_event = {
                    **event,
                    "is_travel": True,
                    "travel_destination": extract_destination_from_summary(event["summary"]),
                    "travel_type": classify_travel_type(event["summary"], event["description"])
                }
                travel_events.append(travel_event)
            
            return {
                "success": True,
                "message": f"여행 일정 {len(travel_events)}개를 찾았습니다.",
                "events": travel_events,
                "total_count": len(travel_events)
            }
        else:
            return result
            
    except Exception as e:
        return {
            "success": False,
            "message": f"여행 일정 조회 중 오류 발생: {str(e)}",
            "events": [],
            "total_count": 0
        }

def get_upcoming_travel_events(days_ahead: int = 30) -> Dict:
    """다가오는 여행 일정 조회"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "success": False,
                "message": "Google Calendar 서비스 연결에 실패했습니다.",
                "events": [],
                "total_count": 0
            }
        
        result = get_upcoming_events(service, days_ahead)
        
        if result["success"]:
            travel_events = []
            travel_keywords = ["여행", "휴가", "관광", "트립", "trip", "travel", "vacation"]
            
            for event in result["events"]:
                summary_lower = event["summary"].lower()
                description_lower = event["description"].lower()
                
                if any(keyword in summary_lower or keyword in description_lower for keyword in travel_keywords):
                    travel_event = {
                        **event,
                        "is_travel": True,
                        "travel_destination": extract_destination_from_summary(event["summary"]),
                        "travel_type": classify_travel_type(event["summary"], event["description"])
                    }
                    travel_events.append(travel_event)
            
            return {
                "success": True,
                "message": f"다가오는 여행 일정 {len(travel_events)}개를 찾았습니다.",
                "events": travel_events,
                "total_count": len(travel_events)
            }
        else:
            return result
            
    except Exception as e:
        return {
            "success": False,
            "message": f"다가오는 여행 일정 조회 중 오류 발생: {str(e)}",
            "events": [],
            "total_count": 0
        }

def search_travel_by_destination(destination: str) -> Dict:
    """목적지별 여행 일정 검색"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "success": False,
                "message": "Google Calendar 서비스 연결에 실패했습니다.",
                "events": [],
                "total_count": 0
            }
        
        result = search_events_by_keyword(service, destination)
        
        if result["success"]:
            matching_events = []
            for event in result["events"]:
                if (destination.lower() in event["summary"].lower() or 
                    destination.lower() in event["description"].lower() or
                    destination.lower() in event["location"].lower()):
                    
                    travel_event = {
                        **event,
                        "is_travel": True,
                        "travel_destination": destination,
                        "travel_type": classify_travel_type(event["summary"], event["description"])
                    }
                    matching_events.append(travel_event)
            
            return {
                "success": True,
                "message": f"{destination} 관련 여행 일정 {len(matching_events)}개를 찾았습니다.",
                "events": matching_events,
                "total_count": len(matching_events)
            }
        else:
            return result
            
    except Exception as e:
        return {
            "success": False,
            "message": f"{destination} 여행 일정 검색 중 오류 발생: {str(e)}",
            "events": [],
            "total_count": 0
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