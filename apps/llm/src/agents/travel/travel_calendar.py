from datetime import datetime, timedelta
import re
from typing import Dict, Optional, Tuple, List
from langchain_core.messages import HumanMessage
from ...utils.calendar_service import (
    get_calendar_service, 
    create_calendar_event,
    get_calendar_events,
    get_upcoming_events,
    search_events_by_keyword,
    get_event_by_id,
    update_calendar_event,
    delete_calendar_event
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

def modify_travel_calendar(messages: List, conversation_state: Dict, llm, event_number: Optional[int] = None) -> Dict:
    """대화를 통해 여행 캘린더 이벤트 수정"""
    try:
        events_result = view_travel_calendar(messages, conversation_state)
        
        if not events_result["success"] or not events_result["calendar_data"].get("events"):
            return {
                "success": False,
                "message": "수정할 여행 일정이 없습니다. 먼저 여행 일정을 조회해주세요.",
                "step": "show_events"
            }
        
        events = events_result["calendar_data"]["events"]
        
        last_user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_message = msg.content
                break
        
        selected_event = None
        if event_number and 1 <= event_number <= len(events):
            selected_event = events[event_number - 1]
        elif len(events) == 1:
            selected_event = events[0]
        
        modification_data = None
        if last_user_message and llm:
            modification_data = understand_modification_request(last_user_message, llm, selected_event)
        
        if selected_event and modification_data:
            return {
                "success": True,
                "message": f"**일정 수정을 진행합니다:**\n\n"
                          f"**대상:** {selected_event.get('summary', '제목 없음')}\n"
                          f"**수정 내용:** {format_modification_summary(modification_data)}\n\n"
                          f"수정을 진행하겠습니다...",
                "step": "execute_modification",
                "selected_event": selected_event,
                "modification_data": modification_data
            }
        
        if not selected_event:
            if event_number and 1 <= event_number <= len(events):
                selected_event = events[event_number - 1]
            elif len(events) == 1:
                selected_event = events[0]
            else:
                event_list = []
                for i, event in enumerate(events, 1):
                    start_date = event.get("start", "").split("T")[0] if "T" in event.get("start", "") else event.get("start", "")
                    event_list.append(f"**{i}.** {event.get('summary', '제목 없음')} ({start_date})")
                
                events_text = '\n'.join(event_list)
                
                return {
                    "success": True,
                    "message": f"수정할 일정을 선택해주세요:\n\n{events_text}\n\n번호를 말씀해주세요 (예: \"1번\", \"첫번째\")",
                    "step": "select_event",
                    "events": events
                }
        
        if selected_event and not modification_data:
            return {
                "success": True,
                "message": f"**선택된 일정:**\n\n"
                          f"**제목:** {selected_event.get('summary', '제목 없음')}  \n"
                          f"**기간:** {selected_event.get('start', '')} ~ {selected_event.get('end', '')}  \n"
                          f"**장소:** {selected_event.get('location', '장소 미정')}  \n\n"
                          f"어떤 내용을 수정하시겠어요? (제목, 날짜, 장소, 설명)",
                "step": "get_modification_details",
                "selected_event": selected_event
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"캘린더 수정 중 오류 발생: {str(e)}",
            "step": "error"
        }

def understand_modification_request(message: str, llm, existing_event: Dict = None) -> Optional[Dict]:
    """LLM을 사용하여 사용자 메시지에서 수정 내용 추출"""
    from datetime import datetime
    from langchain_core.messages import SystemMessage
    import json
    
    current_date = datetime.now()
    
    existing_info = ""
    if existing_event:
        existing_info = f"""
현재 이벤트 정보:
- 제목: {existing_event.get('summary', '')}
- 시작일: {existing_event.get('start', '')}
- 종료일: {existing_event.get('end', '')}
- 장소: {existing_event.get('location', '')}
- 설명: {existing_event.get('description', '')}
"""
    
    system_prompt = f"""사용자가 캘린더 일정을 수정하려고 합니다. 사용자의 메시지에서 수정하려는 내용을 분석해주세요.

{existing_info}

현재 날짜: {current_date.strftime('%Y년 %m월 %d일')}

사용자 메시지: "{message}"

다음 중 수정하려는 내용이 있다면 JSON 형태로 추출해주세요:

{{
    "summary": "새로운 제목 (변경하려는 경우에만)",
    "start_date": "YYYY-MM-DD (시작일 변경하려는 경우에만)",
    "end_date": "YYYY-MM-DD (종료일 변경하려는 경우에만)",
    "location": "새로운 장소 (변경하려는 경우에만)",
    "description": "새로운 설명 (변경하려는 경우에만)"
}}

분석 규칙:
1. 명시적으로 변경하려는 내용만 포함하세요
2. 날짜는 상대적 표현도 절대 날짜로 변환하세요 (예: "내일" → "2024-12-20")
3. 변경하지 않는 필드는 포함하지 마세요
4. 애매한 경우에는 null로 응답하세요
5. 날짜 범위는 "~", "부터", "까지", "에서" 등을 인식하세요

예시:
- "6월 10일~13일로 변경" → {{"start_date": "2024-06-10", "end_date": "2024-06-13"}}
- "제목을 부산여행으로 바꿔" → {{"summary": "부산여행"}}
- "장소를 서울로 수정" → {{"location": "서울"}}
- "내일부터 3일간" → {{"start_date": "2024-12-21", "end_date": "2024-12-23"}}

변경 내용이 없거나 분석할 수 없으면 빈 객체 {{}}를 반환하세요."""
    
    try:
        messages = [SystemMessage(content=system_prompt)]
        response = llm.invoke(messages)
        
        result = json.loads(response.content.strip())
        
        if not result or all(not v for v in result.values()):
            return None
            
        return {k: v for k, v in result.items() if v is not None and v != ""}
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"수정 내용 분석 중 오류: {str(e)}")
        return None

def format_modification_summary(modification_data: Dict) -> str:
    """수정 내용을 읽기 쉽게 포맷팅"""
    summary_parts = []
    
    if modification_data.get('start_date') and modification_data.get('end_date'):
        summary_parts.append(f"날짜: {modification_data['start_date']} ~ {modification_data['end_date']}")
    elif modification_data.get('start_date'):
        summary_parts.append(f"시작일: {modification_data['start_date']}")
    elif modification_data.get('end_date'):
        summary_parts.append(f"종료일: {modification_data['end_date']}")
    
    if modification_data.get('summary'):
        summary_parts.append(f"제목: {modification_data['summary']}")
    
    if modification_data.get('location'):
        summary_parts.append(f"장소: {modification_data['location']}")
    
    if modification_data.get('description'):
        summary_parts.append(f"설명: {modification_data['description']}")
    
    return ', '.join(summary_parts) if summary_parts else "수정 내용 분석 중..."

def delete_travel_calendar(messages: List, conversation_state: Dict, event_number: Optional[int] = None) -> Dict:
    """대화를 통해 여행 캘린더 이벤트 삭제"""
    try:
        events_result = view_travel_calendar(messages, conversation_state)
        
        if not events_result["success"] or not events_result["calendar_data"].get("events"):
            return {
                "success": False,
                "message": "삭제할 여행 일정이 없습니다. 먼저 여행 일정을 조회해주세요.",
                "step": "show_events"
            }
        
        events = events_result["calendar_data"]["events"]
        
        if event_number and 1 <= event_number <= len(events):
            selected_event = events[event_number - 1]
            return {
                "success": True,
                "message": f"**{event_number}번 일정을 삭제하시겠습니까?**\n\n"
                          f"**제목:** {selected_event.get('summary', '제목 없음')}  \n"
                          f"**기간:** {selected_event.get('start', '')} ~ {selected_event.get('end', '')}  \n"
                          f"**장소:** {selected_event.get('location', '장소 미정')}  \n\n"
                          f"삭제하려면 '네' 또는 '삭제'라고 말씀해주세요.",
                "step": "confirm_deletion",
                "selected_event": selected_event
            }
        
        if len(events) == 1:
            selected_event = events[0]
            return {
                "success": True,
                "message": f"**다음 일정을 삭제하시겠습니까?**\n\n"
                          f"**제목:** {selected_event.get('summary', '제목 없음')}  \n"
                          f"**기간:** {selected_event.get('start', '')} ~ {selected_event.get('end', '')}  \n"
                          f"**장소:** {selected_event.get('location', '장소 미정')}  \n\n"
                          f"삭제하려면 '네' 또는 '삭제'라고 말씀해주세요.",
                "step": "confirm_deletion",
                "selected_event": selected_event
            }
        
        event_list = []
        for i, event in enumerate(events, 1):
            start_date = event.get("start", "").split("T")[0] if "T" in event.get("start", "") else event.get("start", "")
            event_list.append(f"**{i}.** {event.get('summary', '제목 없음')} ({start_date})")
        
        events_text = '\n'.join(event_list)
        
        return {
            "success": True,
            "message": f"삭제할 일정을 선택해주세요:\n\n{events_text}\n\n번호를 말씀해주세요 (예: \"1번\", \"첫번째\")",
            "step": "select_event",
            "events": events
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"캘린더 삭제 중 오류 발생: {str(e)}",
            "step": "error"
        }

def execute_event_modification(event_id: str, modifications: Dict) -> Dict:
    """실제 이벤트 수정 실행"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "success": False,
                "message": "Google Calendar 서비스 연결에 실패했습니다."
            }
        
        start_date = None
        end_date = None
        
        if modifications.get("start_date"):
            start_date = datetime.strptime(modifications["start_date"], "%Y-%m-%d")
        if modifications.get("end_date"):
            end_date = datetime.strptime(modifications["end_date"], "%Y-%m-%d")
        
        result = update_calendar_event(
            service=service,
            event_id=event_id,
            summary=modifications.get("summary"),
            start_date=start_date,
            end_date=end_date,
            description=modifications.get("description"),
            location=modifications.get("location")
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"이벤트 수정 실행 중 오류: {str(e)}"
        }

def execute_event_deletion(event_id: str) -> Dict:
    """실제 이벤트 삭제 실행"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "success": False,
                "message": "Google Calendar 서비스 연결에 실패했습니다."
            }
        
        result = delete_calendar_event(service, event_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"이벤트 삭제 실행 중 오류: {str(e)}"
        }

def parse_user_event_selection(message: str) -> Optional[int]:
    """사용자 메시지에서 이벤트 번호 추출"""
    import re
    
    number_pattern = r'(\d+)\s*번'
    match = re.search(number_pattern, message)
    if match:
        return int(match.group(1))
    
    # 순서 표현
    order_map = {
        "첫번째": 1, "첫째": 1, "하나": 1, "1번째": 1,
        "두번째": 2, "둘째": 2, "둘": 2, "2번째": 2,
        "세번째": 3, "셋째": 3, "셋": 3, "3번째": 3,
        "네번째": 4, "넷째": 4, "넷": 4, "4번째": 4,
        "다섯번째": 5, "다섯째": 5, "다섯": 5, "5번째": 5
    }
    
    for pattern, number in order_map.items():
        if pattern in message:
            return number
    
    # 단순 숫자
    digits = re.findall(r'\b(\d+)\b', message)
    if digits:
        return int(digits[0])
    
    return None

def handle_calendar_modification(messages: List, conversation_state: Dict, calendar_data: Dict, llm) -> Dict:
    """캘린더 수정 과정의 전체 상태 관리"""
    last_user_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    event_number = None
    if last_user_message:
        event_number = parse_user_event_selection(last_user_message)
    
    selected_event = calendar_data.get("selected_event")
    current_step = calendar_data.get("modification_step", "start")
    
    if current_step == "start":
        result = modify_travel_calendar(messages, conversation_state, llm, event_number)
        
        new_calendar_data = {
            **calendar_data,
            "modification_step": result.get("step", "error"),
            "events": result.get("events", []),
            "selected_event": result.get("selected_event"),
            "modification_data": result.get("modification_data")
        }
        
        if result.get("step") == "execute_modification":
            selected_event = result.get("selected_event")
            modification_data = result.get("modification_data")
            
            if selected_event and modification_data:
                event_id = selected_event.get("id")
                exec_result = execute_event_modification(event_id, modification_data)
                
                if exec_result["success"]:
                    final_msg = f"✅ **일정이 성공적으로 수정되었습니다!**\n\n{exec_result['message']}"
                else:
                    final_msg = f"❌ **일정 수정에 실패했습니다.**\n\n{exec_result['message']}"
                
                return {
                    "success": True,
                    "message": final_msg,
                    "calendar_data": {
                        **new_calendar_data,
                        "modification_step": "completed"
                    }
                }
        
        return {
            "success": True,
            "message": result["message"],
            "calendar_data": new_calendar_data
        }
    
    elif current_step == "select_event":
        if event_number and calendar_data.get("events"):
            events = calendar_data["events"]
            if 1 <= event_number <= len(events):
                selected_event = events[event_number - 1]
                response_msg = f"**{event_number}번 일정 선택됨:**\n\n" \
                              f"**제목:** {selected_event.get('summary', '제목 없음')}  \n" \
                              f"**기간:** {selected_event.get('start', '')} ~ {selected_event.get('end', '')}  \n" \
                              f"**장소:** {selected_event.get('location', '장소 미정')}  \n\n" \
                              f"어떤 내용을 수정하시겠어요? (제목, 날짜, 장소, 설명)"
                
                return {
                    "success": True,
                    "message": response_msg,
                    "calendar_data": {
                        **calendar_data,
                        "modification_step": "get_modification_details",
                        "selected_event": selected_event
                    }
                }
        
        return {
            "success": True,
            "message": "올바른 번호를 선택해주세요. (예: \"1번\", \"첫번째\")",
            "calendar_data": calendar_data
        }
    
    elif current_step == "get_modification_details":
        if selected_event and last_user_message:
            event_id = selected_event.get("id")
            
            modifications = understand_modification_request(last_user_message, llm, selected_event)
            
            if modifications:
                result = execute_event_modification(event_id, modifications)
                
                if result["success"]:
                    response_msg = f"✅ **일정이 성공적으로 수정되었습니다!**\n\n{result['message']}"
                else:
                    response_msg = f"❌ **일정 수정에 실패했습니다.**\n\n{result['message']}"
            else:
                response_msg = "수정할 내용을 찾을 수 없습니다. 구체적으로 말씀해주세요. (예: \"제목을 부산여행으로 바꿔줘\", \"날짜를 12월 25일로 변경해줘\")"
            
            return {
                "success": True,
                "message": response_msg,
                "calendar_data": {
                    **calendar_data,
                    "modification_step": "completed"
                }
            }
    
    return {
        "success": False,
        "message": "수정 과정에서 문제가 발생했습니다. 다시 시도해주세요.",
        "calendar_data": calendar_data
    }

def handle_calendar_deletion(messages: List, conversation_state: Dict, calendar_data: Dict, llm) -> Dict:
    """캘린더 삭제 과정의 전체 상태 관리"""
    last_user_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    event_number = None
    if last_user_message:
        event_number = parse_user_event_selection(last_user_message)
    
    selected_event = calendar_data.get("selected_event")
    current_step = calendar_data.get("deletion_step", "start")
    
    if current_step == "start":
        result = delete_travel_calendar(messages, conversation_state, event_number)
        
        new_calendar_data = {
            **calendar_data,
            "deletion_step": result.get("step", "error"),
            "events": result.get("events", []),
            "selected_event": result.get("selected_event")
        }
        
        return {
            "success": True,
            "message": result["message"],
            "calendar_data": new_calendar_data
        }
    
    elif current_step == "select_event":
        if event_number and calendar_data.get("events"):
            events = calendar_data["events"]
            if 1 <= event_number <= len(events):
                selected_event = events[event_number - 1]
                response_msg = f"**{event_number}번 일정을 삭제하시겠습니까?**\n\n" \
                              f"**제목:** {selected_event.get('summary', '제목 없음')}  \n" \
                              f"**기간:** {selected_event.get('start', '')} ~ {selected_event.get('end', '')}  \n" \
                              f"**장소:** {selected_event.get('location', '장소 미정')}  \n\n" \
                              f"삭제하려면 '네' 또는 '삭제'라고 말씀해주세요."
                
                return {
                    "success": True,
                    "message": response_msg,
                    "calendar_data": {
                        **calendar_data,
                        "deletion_step": "confirm_deletion",
                        "selected_event": selected_event
                    }
                }
        
        return {
            "success": True,
            "message": "올바른 번호를 선택해주세요. (예: \"1번\", \"첫번째\")",
            "calendar_data": calendar_data
        }
    
    elif current_step == "confirm_deletion":
        if selected_event and last_user_message:
            confirmation_keywords = ["네", "예", "삭제", "확인", "맞습니다", "그래요", "맞아요", "삭제해줘", "지워줘"]
            cancellation_keywords = ["아니요", "취소", "안 해요", "그만", "아니"]
            
            message_lower = last_user_message.lower().strip()
            
            print(f"DEBUG: 사용자 메시지 = '{last_user_message}', 소문자 = '{message_lower}'")
            print(f"DEBUG: 확인 키워드 체크 = {[keyword for keyword in confirmation_keywords if keyword in message_lower]}")
            
            if any(keyword in message_lower for keyword in confirmation_keywords):
                event_id = selected_event.get("id")
                print(f"DEBUG: 삭제 실행 중... event_id = {event_id}")
                
                result = execute_event_deletion(event_id)
                
                if result["success"]:
                    response_msg = f"✅ **일정이 성공적으로 삭제되었습니다!**\n\n{result['message']}"
                else:
                    response_msg = f"❌ **일정 삭제에 실패했습니다.**\n\n{result['message']}"
                
                return {
                    "success": True,
                    "message": response_msg,
                    "calendar_data": {
                        **calendar_data,
                        "deletion_step": "completed",
                        "selected_event": None
                    }
                }
            
            elif any(keyword in message_lower for keyword in cancellation_keywords):
                return {
                    "success": True,
                    "message": "일정 삭제가 취소되었습니다.",
                    "calendar_data": {
                        **calendar_data,
                        "deletion_step": "cancelled",
                        "selected_event": None
                    }
                }
            
            else:
                return {
                    "success": True,
                    "message": "'네' 또는 '아니요'로 답변해주세요. 정말 삭제하시겠습니까?",
                    "calendar_data": calendar_data
                }
        else:
            return {
                "success": False,
                "message": "삭제할 일정 정보를 찾을 수 없습니다. 다시 시도해주세요.",
                "calendar_data": {
                    **calendar_data,
                    "deletion_step": "error"
                }
            }
    
    return {
        "success": False,
        "message": "삭제 과정에서 문제가 발생했습니다. 다시 시도해주세요.",
        "calendar_data": calendar_data
    } 