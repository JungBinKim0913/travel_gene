from typing import Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from datetime import datetime
from .calendar import (
    register_travel_calendar, 
    view_travel_calendar, 
    handle_calendar_modification,
    handle_calendar_deletion
)

from .types import ConversationState
from .utils import select_next_question, create_context_message, analyze_preferences, analyze_user_intent
from .guardrail import check_content_safety
from ...utils.openai_utils import analyze_conversation_with_json_structure
from ...utils.kakao_map_api import get_kakao_map_api

def check_guardrail(llm, state: Dict) -> Dict:
    """보안 및 안전성 검사"""
    try:
        messages = state.get("messages", [])
        
        if not messages:
            return {
                **state,
                "current_step": str(ConversationState.UNDERSTAND_REQUEST)
            }
        
        last_user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_message = msg.content
                break
        
        if not last_user_message:
            return {
                **state,
                "current_step": str(ConversationState.UNDERSTAND_REQUEST)
            }
        
        safety_check = check_content_safety(llm, last_user_message)
        
        if not safety_check["is_safe"]:
            response = AIMessage(content=safety_check["warning_message"])
            messages.append(response)
            
            return {
                **state,
                "messages": messages,
                "current_step": str(ConversationState.END),
                "guardrail_violation": safety_check["violation_type"]
            }
        
        return {
            **state,
            "current_step": str(ConversationState.UNDERSTAND_REQUEST)
        }
        
    except Exception as e:
        print(f"Error in check_guardrail: {str(e)}")
        return {
            **state,
            "current_step": str(ConversationState.UNDERSTAND_REQUEST)
        } 

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
        else:
            # 기존 conversation_state가 있으면 기본값만 보완
            conversation_state.setdefault("destination", None)
            conversation_state.setdefault("travel_dates", None)
            conversation_state.setdefault("duration", None)
            conversation_state.setdefault("preferences", [])
            conversation_state.setdefault("details_collected", False)
            conversation_state.setdefault("last_topic", None)
            conversation_state.setdefault("pending_questions", [])
            conversation_state.setdefault("confirmed_info", set())
            conversation_state.setdefault("context_keywords", set())
            conversation_state.setdefault("interaction_history", [])
        
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
        
        # plan_data 존재 여부 확인 - JSON 형식과 텍스트 형식 모두 지원
        has_plan = bool(plan_data.get("content") or plan_data.get("plan_data"))
        
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
                if primary_intent == "캘린더 조회 요청":
                    return str(ConversationState.VIEW_CALENDAR)
                
                if primary_intent == "캘린더 등록 요청":
                    if has_plan:
                        return str(ConversationState.REGISTER_CALENDAR)
                    elif has_destination and has_dates and has_preferences:
                        messages.append(SystemMessage(content="""
                        캘린더에 등록하려면 먼저 여행 계획이 필요합니다. 
                        지금까지 수집된 정보를 바탕으로 여행 계획을 생성한 후 캘린더에 등록하겠습니다.
                        """))
                        return str(ConversationState.GENERATE_PLAN)
                
                if primary_intent == "캘린더 수정 요청":
                    return str(ConversationState.MODIFY_CALENDAR)
                
                if primary_intent == "캘린더 삭제 요청":
                    return str(ConversationState.DELETE_CALENDAR)
                
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
            
            content_lower = content.lower()
            plan_keywords = ["계획", "스케줄", "플랜", "짜줘"]
            
            if any(keyword in content_lower for keyword in plan_keywords):
                if has_destination and has_dates and has_preferences:
                    return str(ConversationState.GENERATE_PLAN)
            
            if ("그대로" in content_lower or "이대로" in content_lower) and any(keyword in content_lower for keyword in ["계획", "진행", "시작"]):
                if has_destination and has_dates and has_preferences:
                    return str(ConversationState.GENERATE_PLAN)
        
        if not has_destination:
            return str(ConversationState.ASK_DESTINATION)
        
        if not has_dates:
            return str(ConversationState.COLLECT_DETAILS)
        
        if not has_preferences:
            return str(ConversationState.COLLECT_DETAILS)
        
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

    destination = conversation_state.get('destination', '미정')
    preferences = conversation_state.get('preferences', [])
    
    collected_info = f"""현재까지 파악된 여행 정보:
    - 여행지: {destination}
    - 여행 기간: {conversation_state.get('travel_dates', '미정')}
    - 선호 사항: {preferences}
    """

    real_places_info = ""
    places_found = False
    
    kakao_api = get_kakao_map_api()
    
    if kakao_api and destination != '미정' and preferences:
        try:
            places_by_preference = kakao_api.get_places_by_preferences(destination, preferences)
            
            if places_by_preference:
                real_places_info = "\n\n=== 🗺️ 실제 추천 장소 정보 ===\n"
                total_places = 0
                
                for preference, places in places_by_preference.items():
                    if places:
                        real_places_info += f"\n📍 {preference} 관련 장소:\n"
                        
                        top_places = places[:5]
                        for i, place in enumerate(top_places, 1):
                            real_places_info += f"  {i}. {place['name']}\n"
                            real_places_info += f"     📍 {place['address']}\n"
                            if place.get('phone'):
                                real_places_info += f"     📞 {place['phone']}\n"
                            real_places_info += f"     🏷️ {place['category']}\n\n"
                        
                        total_places += len(top_places)
                
                if total_places > 0:
                    places_found = True
                    real_places_info += f"💡 총 {total_places}개의 실제 장소 정보를 찾았습니다.\n"
                
        except Exception as e:
            real_places_info = "\n\n⚠️ 실시간 장소 정보 검색에 일시적인 문제가 발생했습니다. 일반적인 추천 정보를 제공합니다.\n"

    if places_found:
        plan_instruction = f"""{collected_info}

위 정보를 바탕으로 수집된 실제 장소 정보를 활용하여 여행 계획을 생성해주세요:

{real_places_info}

**중요: 응답을 반드시 다음 JSON 형식으로 작성해주세요. 다른 텍스트 없이 JSON만 반환해주세요:**

{{
  "travel_overview": {{
    "destination": "목적지명",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", 
    "duration_days": 숫자,
    "summary": "여행 개요 설명"
  }},
  "itinerary": [
    {{
      "date": "YYYY-MM-DD",
      "day_of_week": "요일",
      "activities": [
        {{
          "time": "HH:MM",
          "title": "활동명",
          "location": "장소명",
          "address": "실제 주소",
          "description": "활동 설명",
          "category": "식사|관광|숙박|이동|쇼핑|휴식",
          "duration_minutes": 예상소요시간(분)
        }}
      ]
    }}
  ],
  "preparation": {{
    "essential_items": ["필수 준비물 목록"],
    "reservations_needed": ["사전 예약 필요 사항"],
    "local_tips": ["현지 정보"],
    "warnings": ["주의사항"]
  }},
  "alternatives": {{
    "rainy_day_options": ["우천시 대체 장소"],
    "optional_activities": ["선택적 추가 활동"]
  }}
}}

**참고:** 실제 수집된 장소 정보를 최대한 활용하여 구체적이고 실용적인 계획을 JSON 형식으로 작성해주세요."""
    else:
        plan_instruction = f"""{collected_info}

위 정보를 바탕으로 여행 계획을 생성해주세요. 부족한 정보는 일반적인 선호도를 반영하여 채워주세요.

**중요: 응답을 반드시 다음 JSON 형식으로 작성해주세요. 다른 텍스트 없이 JSON만 반환해주세요:**

{{
  "travel_overview": {{
    "destination": "목적지명",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "duration_days": 숫자,
    "summary": "여행 개요 설명"
  }},
  "itinerary": [
    {{
      "date": "YYYY-MM-DD", 
      "day_of_week": "요일",
      "activities": [
        {{
          "time": "HH:MM",
          "title": "활동명",
          "location": "장소명", 
          "address": "주소",
          "description": "활동 설명",
          "category": "식사|관광|숙박|이동|쇼핑|휴식",
          "duration_minutes": 예상소요시간(분)
        }}
      ]
    }}
  ],
  "preparation": {{
    "essential_items": ["필수 준비물 목록"],
    "reservations_needed": ["사전 예약 필요 사항"], 
    "local_tips": ["현지 정보"],
    "warnings": ["주의사항"]
  }},
  "alternatives": {{
    "rainy_day_options": ["우천시 대체 장소"],
    "optional_activities": ["선택적 추가 활동"]
  }}
}}"""

    messages.append(SystemMessage(content=plan_instruction))

    response = llm.invoke(messages)
    messages.append(response)
    
    try:
        import json
        plan_json = json.loads(response.content.strip())
        
        plan_metadata = {
            "generated_at": "generate_plan",
            "plan_data": plan_json,
            "collected_info": collected_info,
            "kakao_places_used": places_found,
            "places_count": sum(len(places) for places in places_by_preference.values()) if places_found else 0,
            "format": "json"
        }
    except json.JSONDecodeError as e:
        plan_metadata = {
            "generated_at": "generate_plan",
            "content": response.content,
            "collected_info": collected_info,
            "kakao_places_used": places_found,
            "places_count": sum(len(places) for places in places_by_preference.values()) if places_found else 0,
            "format": "text"
        }
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.GENERATE_PLAN),
        "plan_data": plan_metadata
    }

def refine_plan(llm, state: Dict) -> Dict:
    """여행 계획 수정"""
    messages = state.get("messages", [])
    plan_data = state.get("plan_data", {})
    conversation_state = state.get("conversation_state", {})
    
    used_kakao_before = plan_data.get("kakao_places_used", False)
    destination = conversation_state.get('destination', '미정')
    preferences = conversation_state.get('preferences', [])
    
    additional_places_info = ""
    
    if destination != '미정' and preferences and not used_kakao_before:
        kakao_api = get_kakao_map_api()
        if kakao_api:
            try:
                places_by_preference = kakao_api.get_places_by_preferences(destination, preferences)
                if places_by_preference:
                    additional_places_info = "\n\n🆕 **추가 참고 장소 정보:**\n"
                    for preference, places in places_by_preference.items():
                        if places:
                            additional_places_info += f"\n📍 {preference} 관련:\n"
                            for i, place in enumerate(places[:3], 1):
                                additional_places_info += f"  • {place['name']} ({place['address']})\n"
                    additional_places_info += "\n"
            except Exception:
                pass

    refine_instruction = f"""사용자의 피드백을 반영하여 기존 여행 계획을 수정해주세요.

🔄 **수정 지침:**
1. 사용자의 구체적인 요청사항을 우선 반영
2. 기존 계획의 좋은 부분은 유지
3. 변경된 부분을 명확히 표시
4. 실현 가능하고 현실적인 대안 제시

{additional_places_info}

📝 **수정된 계획 형식:**
## 🔄 계획 수정 사항
- **변경 내용:** [구체적인 변경사항]
- **변경 이유:** [사용자 요청 반영]

## 📅 수정된 여행 일정
[수정된 전체 일정 또는 변경된 부분만]

💡 **변경사항 요약:**
- ✅ 추가된 내용
- 🔄 수정된 내용  
- ❌ 제거된 내용

기존 계획을 기반으로 자연스럽게 수정해주세요."""

    messages.append(SystemMessage(content=refine_instruction))

    response = llm.invoke(messages)
    messages.append(response)
    
    refined_metadata = {
        "generated_at": "refine_plan",
        "content": response.content,
        "previous_plan": plan_data.get("content") or plan_data.get("plan_data", ""),
        "kakao_places_used": used_kakao_before or bool(additional_places_info),
        "refinement_enhanced": bool(additional_places_info)
    }
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.REFINE_PLAN),
        "plan_data": refined_metadata
    }

def register_calendar(llm, state: Dict) -> Dict:
    """여행 계획을 Google Calendar에 등록"""
    messages = state.get("messages", [])
    plan_data = state.get("plan_data", {})
    
    # plan_data 존재 여부 확인 - JSON 형식과 텍스트 형식 모두 지원
    if not (plan_data.get("content") or plan_data.get("plan_data")):
        error_msg = "Google Calendar 등록에 필요한 여행 계획 정보가 없습니다. 먼저 여행 계획을 생성해주세요."
        response = AIMessage(content=error_msg)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_step": str(ConversationState.UNDERSTAND_REQUEST)
        }
    
    calendar_result = register_travel_calendar(plan_data)
    
    if calendar_result["success"]:
        calendar_msg = f"""여행 계획이 Google Calendar에 성공적으로 등록되었습니다.
        
        - 등록된 일정 수: {calendar_result['events_count']}개
        
        모든 일정은 Google Calendar에서 확인하실 수 있습니다.
        추가 수정이 필요하시면 Google Calendar에서 직접 수정하시거나 말씀해주세요."""
    else:
        calendar_msg = f"""죄송합니다. Google Calendar 등록 중 문제가 발생했습니다.
        
        - 오류 메시지: {calendar_result['message']}
        
        다시 시도해보시겠어요?"""
    
    response = AIMessage(content=calendar_msg)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.REGISTER_CALENDAR),
        "calendar_data": calendar_result
    }

def view_calendar(llm, state: Dict) -> Dict:
    """Google Calendar에서 여행 일정 조회"""
    messages = state.get("messages", [])
    conversation_state = state.get("conversation_state", {})
    
    result = view_travel_calendar(messages, conversation_state)
    
    response = AIMessage(content=result["message"])
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.VIEW_CALENDAR),
        "calendar_data": result["calendar_data"]
    }

def modify_calendar(llm, state: Dict) -> Dict:
    """Calendar에서 여행 일정 수정"""
    messages = state.get("messages", [])
    conversation_state = state.get("conversation_state", {})
    calendar_data = state.get("calendar_data", {})
    
    result = handle_calendar_modification(messages, conversation_state, calendar_data, llm)
    
    response = AIMessage(content=result["message"])
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.MODIFY_CALENDAR),
        "calendar_data": result["calendar_data"]
    }

def delete_calendar(llm, state: Dict) -> Dict:
    """Google Calendar에서 여행 일정 삭제"""
    messages = state.get("messages", [])
    conversation_state = state.get("conversation_state", {})
    calendar_data = state.get("calendar_data", {})
    
    result = handle_calendar_deletion(messages, conversation_state, calendar_data, llm)
    
    response = AIMessage(content=result["message"])
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "current_step": str(ConversationState.DELETE_CALENDAR),
        "calendar_data": result["calendar_data"]
    }
