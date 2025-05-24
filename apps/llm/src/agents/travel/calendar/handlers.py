from typing import Dict, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage
from ....utils.calendar_service import (
    get_calendar_service,
    update_calendar_event,
    delete_calendar_event
)
from .actions import view_travel_calendar
from .utils import (
    parse_user_event_selection,
    understand_modification_request,
    format_modification_summary
)

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