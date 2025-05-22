from typing import Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from datetime import datetime
import json

from .types import ConversationState
from .utils import select_next_question, create_context_message, analyze_preferences, analyze_user_intent
from .calendar_utils import create_calendar_events
from .openai_utils import analyze_conversation_with_json_structure

def understand_request(llm, state: Dict) -> Dict:
    """사용자 요청 이해"""
    try:
        messages = state.get("messages", [])
        conversation_state = state.get("conversation_state", {})
        memory_size = state.get("memory_size", 10)
        
        if not conversation_state:
            conversation_state = {
                "destination": None,
                "travel_dates": None,
                "duration": None,
                "preferences": [],
                "details_collected": False,
                "last_topic": None,
                "pending_questions": [],
                "confirmed_info": set(),
                "context_keywords": set(),
                "interaction_history": []
            }
        
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages.insert(0, SystemMessage(content="""여행 계획을 도와드리는 AI 어시스턴트입니다.
            자연스러운 대화를 통해 맞춤형 여행 계획을 만들어드리겠습니다.
            
            제가 도와드릴 수 있는 것들:
            1. 여행지 추천
            2. 일정 계획
            3. 예산 관리
            4. 맛집/관광지 추천
            5. 교통편 안내"""))
        
        last_messages = messages[-memory_size:] if len(messages) >= 3 else messages
        current_year = datetime.now().year
        
        analysis_result = analyze_conversation_with_json_structure(llm, last_messages, current_year)
        
        try:
            if destination := analysis_result.get("core_info", {}).get("destination"):
                conversation_state["destination"] = destination
            
            if date_info := analysis_result.get("core_info", {}).get("date_validation"):
                if not date_info.get("is_valid", True) and date_info.get("corrected"):
                    conversation_state["travel_dates"] = date_info["corrected"]
                elif dates := analysis_result.get("core_info", {}).get("dates"):
                    conversation_state["travel_dates"] = dates
            
            if duration := analysis_result.get("core_info", {}).get("duration"):
                conversation_state["duration"] = duration
                conversation_state["confirmed_info"].add("travel_dates")
            
            if preferences := analysis_result.get("core_info", {}).get("preferences"):
                current_preferences = set(conversation_state.get("preferences", []))
                current_preferences.update(preferences)
                conversation_state["preferences"] = list(current_preferences)
            
            context_data = analysis_result.get("context", {})
            conversation_state["last_topic"] = context_data.get("current_topic", conversation_state.get("last_topic"))
            
            user_interests = context_data.get("user_interests", [])
            if user_interests:
                current_keywords = set(conversation_state.get("context_keywords", set()))
                current_keywords.update(user_interests)
                conversation_state["context_keywords"] = current_keywords
            
            next_steps = analysis_result.get("next_steps", {})
            required_info = set(next_steps.get("required_info", []))
            
            if required_info:
                confirmed = set(conversation_state.get("confirmed_info", set()))
                conversation_state["pending_questions"] = list(required_info - confirmed)
            
            conversation_state["interaction_history"].append({
                "timestamp": datetime.now().isoformat(),
                "topic": conversation_state["last_topic"],
                "collected_info": list(required_info & conversation_state.get("confirmed_info", set()))
            })
            
        except Exception as e:
            print(f"Error processing analysis result: {str(e)}")
        
        context_msg = create_context_message(conversation_state)
        if context_msg:
            messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
            messages.insert(0, context_msg)
        
        if conversation_state["pending_questions"]:
            next_question = select_next_question(
                conversation_state["pending_questions"],
                conversation_state["last_topic"],
                conversation_state["interaction_history"]
            )
            if next_question:
                if not any(info in next_question.lower() for info in conversation_state["confirmed_info"]):
                    response_prompt = SystemMessage(content=f"""현재까지 파악된 정보를 바탕으로 자연스럽게 대화를 이어가주세요.
                    
                    다음 정보가 필요합니다: {next_question}
                    
                    대화 스타일:
                    1. 친근하고 자연스러운 어조 유지
                    2. 이전 대화 내용을 참고하여 맥락 유지
                    3. 열린 질문으로 시작하여 사용자의 선호도를 자세히 파악
                    4. 적절한 예시나 추천사항 포함
                    5. 한 번에 너무 많은 것을 물어보지 않기
                    6. 이미 알고 있는 정보는 다시 물어보지 않기""")
                    
                    messages.append(response_prompt)
        
        response = llm.invoke(messages)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_step": str(ConversationState.UNDERSTAND_REQUEST),
            "conversation_state": conversation_state
        }
    except Exception as e:
        print(f"Error in understand_request: {str(e)}")
        return {
            **state,
            "messages": messages if 'messages' in locals() else [],
            "current_step": str(ConversationState.UNDERSTAND_REQUEST),
            "conversation_state": conversation_state if 'conversation_state' in locals() else {}
        }

def determine_next_step(state: Dict) -> str:
    """다음 대화 단계 결정"""
    try:
        messages = state.get("messages", [])
        conversation_state = state.get("conversation_state", {})
        plan_data = state.get("plan_data", {})
        llm = state.get("llm")
        
        has_destination = bool(conversation_state.get("destination"))
        has_dates = bool(conversation_state.get("travel_dates"))
        has_preferences = bool(conversation_state.get("preferences"))
        
        has_plan = bool(plan_data.get("content"))
        
        if not has_destination:
            return str(ConversationState.ASK_DESTINATION)
        
        if not has_dates:
            return str(ConversationState.COLLECT_DETAILS)
        
        if not has_preferences:
            return str(ConversationState.COLLECT_DETAILS)
        
        last_user_message = None
        previous_ai_message = None
        
        for i, msg in enumerate(reversed(messages)):
            if isinstance(msg, HumanMessage) and last_user_message is None:
                last_user_message = msg
            elif isinstance(msg, AIMessage) and previous_ai_message is None and last_user_message is not None:
                previous_ai_message = msg
                break
        
        if last_user_message and llm:
            content = last_user_message.content
            previous_content = previous_ai_message.content if previous_ai_message else None
            
            intent_analysis = analyze_user_intent(llm, content, has_plan, previous_content)
            
            print(f"Intent analysis: {intent_analysis}")
            
            primary_intent = intent_analysis.get("primary_intent", "일반 대화")
            confidence = intent_analysis.get("confidence", 0.0)
            is_affirmative = intent_analysis.get("is_affirmative_to_previous", False)
            
            CONFIDENCE_THRESHOLD = 0.7
            
            if confidence >= CONFIDENCE_THRESHOLD:
                if primary_intent == "캘린더 등록 요청":
                    if has_plan:
                        return str(ConversationState.REGISTER_CALENDAR)
                    elif has_destination and has_dates and has_preferences:
                        messages.append(SystemMessage(content="""
                        캘린더에 등록하려면 먼저 여행 계획이 필요합니다. 
                        지금까지 수집된 정보를 바탕으로 여행 계획을 생성한 후 캘린더에 등록하겠습니다.
                        """))
                        return str(ConversationState.GENERATE_PLAN)
                
                if primary_intent == "여행 계획 생성 요청":
                    if has_destination and has_dates and has_preferences:
                        return str(ConversationState.GENERATE_PLAN)
                
                if primary_intent == "계획 수정 요청":
                    if has_plan:
                        return str(ConversationState.REFINE_PLAN)
                    elif has_destination and has_dates and has_preferences:
                        messages.append(SystemMessage(content="""
                        수정할 여행 계획이 아직 없습니다. 
                        먼저 기본 여행 계획을 생성한 후 수정하겠습니다.
                        """))
                        return str(ConversationState.GENERATE_PLAN)
                
                if primary_intent == "긍정 응답" and is_affirmative and previous_ai_message:
                    prev_content = previous_ai_message.content.lower()
                    
                    plan_suggestion_keywords = ["계획", "일정", "만들어", "드릴까요", "작성해", "생성"]
                    if any(keyword in prev_content for keyword in plan_suggestion_keywords) and has_destination and has_dates and has_preferences:
                        return str(ConversationState.GENERATE_PLAN)
                    
                    calendar_suggestion_keywords = ["캘린더", "등록", "추가", "구글", "일정에"]
                    if any(keyword in prev_content for keyword in calendar_suggestion_keywords) and has_plan:
                        return str(ConversationState.REGISTER_CALENDAR)
                    
                    refine_suggestion_keywords = ["수정", "변경", "조정", "바꿔", "고쳐"]
                    if any(keyword in prev_content for keyword in refine_suggestion_keywords) and has_plan:
                        return str(ConversationState.REFINE_PLAN)
            
            else:
                content_lower = content.lower()
                plan_keywords = ["계획", "일정", "스케줄", "플랜", "짜줘"]
                calendar_keywords = ["캘린더", "일정", "등록", "구글", "캘린더에", "달력"]
                
                if has_plan and any(keyword in content_lower for keyword in calendar_keywords):
                    return str(ConversationState.REGISTER_CALENDAR)
                
                if any(keyword in content_lower for keyword in plan_keywords):
                    if has_destination and has_dates and has_preferences:
                        return str(ConversationState.GENERATE_PLAN)
                
                if ("그대로" in content_lower or "이대로" in content_lower) and any(keyword in content_lower for keyword in ["계획", "진행", "시작"]):
                    if has_destination and has_dates and has_preferences:
                        return str(ConversationState.GENERATE_PLAN)
        
        return str(ConversationState.UNDERSTAND_REQUEST)
        
    except Exception as e:
        print(f"Error in determine_next_step: {str(e)}")
        return str(ConversationState.END)

def ask_destination(llm, state: Dict) -> Dict:
    """여행지 문의"""
    messages = state.get("messages", [])
    conversation_state = state.get("conversation_state", {})
    memory_size = state.get("memory_size", 10)
    
    previous_preferences = analyze_preferences(llm, messages, memory_size)
    
    if previous_preferences:
        preferences_str = ", ".join(previous_preferences)
        destination_prompt = SystemMessage(content=f"""지금까지 파악된 선호도는 다음과 같습니다:
        {preferences_str}
        
        이러한 선호도를 고려하여 구체적인 여행지나 관련 장소를 추천해주세요.
        이미 특정 지역이 언급되었다면, 그 지역 내에서 적합한 장소들을 추천해주세요.
        
        추천 시 고려사항:
        1. 선호도와 일치하는 장소 우선
        2. 계절/날씨 고려
        3. 이동 편의성
        4. 주변 관광지와의 연계성
        5. 현지 특색""")
    else:
        destination_prompt = SystemMessage(content="""어떤 여행을 원하시는지 자연스럽게 물어보세요.
        예시:
        1. 특정 여행지를 언급했다면 확인
        2. 선호하는 여행 스타일이나 원하는 경험 파악
        3. 여행지 추천이 필요하다면 몇 가지 옵션 제시
        
        대화 가이드:
        1. 열린 질문으로 시작
        2. 구체적인 예시 포함
        3. 단계적으로 선호도 파악
        4. 맥락 유지""")
    
    messages.append(destination_prompt)
    response = llm.invoke(messages)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.ASK_DESTINATION),
        "conversation_state": {
            **conversation_state,
            "preferences": previous_preferences
        }
    }

def collect_details(llm, state: Dict) -> Dict:
    """세부 정보 수집"""
    messages = state.get("messages", [])
    conversation_state = state.get("conversation_state", {})
    
    missing_info = []
    if not conversation_state.get("travel_dates"):
        missing_info.append("여행 기간")
    if not conversation_state.get("preferences"):
        missing_info.append("선호하는 활동")
        
    if missing_info:
        details_prompt = SystemMessage(content=f"""자연스러운 대화로 다음 정보를 물어보세요:
        - {', '.join(missing_info)}
        한 번에 너무 많은 것을 물어보지 말고, 대화를 이어나가듯이 질문해주세요.""")
        
        messages.append(details_prompt)
        response = llm.invoke(messages)
        messages.append(response)
    else:
        conversation_state["details_collected"] = True
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.COLLECT_DETAILS),
        "conversation_state": conversation_state
    }

def generate_plan(llm, state: Dict) -> Dict:
    """여행 계획 생성"""
    messages = state.get("messages", [])
    conversation_state = state.get("conversation_state", {})

    collected_info = f"""현재까지 파악된 여행 정보:
    - 여행지: {conversation_state.get('destination', '미정')}
    - 여행 기간: {conversation_state.get('travel_dates', '미정')}
    - 선호 사항: {conversation_state.get('preferences', '미정')}
    """

    messages.append(SystemMessage(content=f"""{collected_info}

    위 정보를 바탕으로 여행 계획을 생성해주세요. 부족한 정보는 일반적인 선호도를 반영하여 채워주세요.
    응답은 다음 형식으로 작성해주세요:

    1. 여행 개요
       - 기간
       - 목적지
       - 주요 일정 개요

    2. 일자별 세부 일정
       [각 일자별로]
       - 날짜와 요일
       - 시간대별 활동 계획
       - 이동 수단 및 소요 시간
       - 식사 계획

    3. 준비사항
       - 필수 준비물
       - 사전 예약 필요 사항
       - 현지 정보
       - 주의사항
       - 추천 사항

    4. 대체 옵션
       - 우천시 대체 일정
       - 선택적 추가 활동"""))

    response = llm.invoke(messages)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.GENERATE_PLAN),
        "plan_data": {
            "generated_at": "generate_plan",
            "content": response.content,
            "collected_info": collected_info
        }
    }

def refine_plan(llm, state: Dict) -> Dict:
    """여행 계획 수정"""
    messages = state.get("messages", [])
    plan_data = state.get("plan_data", {})

    messages.append(SystemMessage(content="""사용자의 피드백을 반영하여 기존 계획을 수정해주세요.
    변경된 부분을 명확히 표시해주세요."""))

    response = llm.invoke(messages)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.REFINE_PLAN),
        "plan_data": {
            "generated_at": "refine_plan",
            "content": response.content,
            "previous_plan": plan_data.get("content", "")
        }
    }

def register_calendar(llm, state: Dict) -> Dict:
    """여행 계획을 Google Calendar에 등록"""
    messages = state.get("messages", [])
    plan_data = state.get("plan_data", {})
    
    if not plan_data.get("content"):
        error_msg = "Google Calendar 등록에 필요한 여행 계획 정보가 없습니다. 먼저 여행 계획을 생성해주세요."
        messages.append(SystemMessage(content=error_msg))
        response = llm.invoke(messages)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_step": str(ConversationState.UNDERSTAND_REQUEST)
        }
    
    calendar_result = create_calendar_events(plan_data)
    
    if calendar_result["success"]:
        calendar_msg = f"""여행 계획이 Google Calendar에 성공적으로 등록되었습니다.
        
        - 등록된 일정 수: {calendar_result['events_count']}개
        
        모든 일정은 Google Calendar에서 확인하실 수 있습니다.
        추가 수정이 필요하시면 Google Calendar에서 직접 수정하시거나 말씀해주세요."""
    else:
        calendar_msg = f"""죄송합니다. Google Calendar 등록 중 문제가 발생했습니다.
        
        - 오류 메시지: {calendar_result['message']}
        
        다시 시도해보시겠어요?"""
    
    calendar_prompt = SystemMessage(content=calendar_msg)
    messages.append(calendar_prompt)
    
    response = llm.invoke(messages)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.REGISTER_CALENDAR),
        "calendar_data": calendar_result
    } 