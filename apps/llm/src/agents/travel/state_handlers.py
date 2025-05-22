from typing import Dict
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime
import json

from .types import ConversationState
from .utils import select_next_question, create_context_message, analyze_preferences

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
        analysis_prompt = SystemMessage(content=f"""당신은 여행 대화 분석 전문가입니다. 주어진 대화 내용을 분석하여 정확히 아래 JSON 형식으로만 응답해야 합니다.

        당신의 임무:
        1. 대화에서 명시적으로 언급된 정보만 추출
        2. 추측이나 가정은 절대 하지 않음
        3. 아래 형식을 정확히 준수
        4. 한글이 아닌 정확한 JSON 키 사용
        5. 여행 기간은 구체적인 날짜가 없더라도 "2박 3일"과 같은 형식도 인식
        6. 날짜 처리 시 다음 규칙을 따를 것:
           - 연도가 없는 경우 현재 연도({current_year}) 사용
           - 날짜가 있는 경우 반드시 요일을 확인하고 포함
           - 날짜 형식은 "YYYY년 MM월 DD일 (요일)" 형식으로 통일
           - 다양한 날짜 표현을 이해하고 처리 (예: "이번 주 토요일", "다음 달 초", "크리스마스")
           - 잘못된 날짜나 요일 조합이 있는 경우 올바른 정보로 수정

        응답 형식 (이 형식을 정확히 따라야 함):
        {{
            "core_info": {{
                "destination": "목적지명 또는 null",
                "dates": "여행날짜 또는 null (형식: YYYY년 MM월 DD일 (요일))",
                "duration": "숙박일수 (예: 2) 또는 null",
                "date_validation": {{
                    "is_valid": true/false,
                    "original": "원본 날짜 표현",
                    "corrected": "수정된 날짜 (필요한 경우)"
                }},
                "preferences": ["선호도1", "선호도2"]
            }},
            "context": {{
                "current_topic": "현재 주제",
                "related_to_previous": true,
                "user_interests": ["관심사1", "관심사2"]
            }},
            "next_steps": {{
                "required_info": ["필요정보1", "필요정보2"],
                "suggested_questions": ["질문1", "질문2"],
                "recommendations": ["제안1", "제안2"]
            }}
        }}

        날짜 처리 예시:
        1. "다음 주 토요일" -> "{current_year}년 MM월 DD일 (토)"
        2. "크리스마스" -> "{current_year}년 12월 25일 (수)"
        3. "6월 7일" -> "{current_year}년 6월 7일 (금)"
        
        잘못된 날짜/요일 조합 예시:
        입력: "{current_year}년 6월 7일 (토)" -> 수정: "{current_year}년 6월 7일 (금)" (실제 요일로 수정)""")
        
        analysis_messages = [analysis_prompt, *last_messages]
        analysis_response = llm.invoke(analysis_messages)
        
        try:
            analysis_result = json.loads(analysis_response.content)
            
            if destination := analysis_result["core_info"].get("destination"):
                conversation_state["destination"] = destination
            
            if date_info := analysis_result["core_info"].get("date_validation"):
                if not date_info["is_valid"] and date_info.get("corrected"):
                    conversation_state["travel_dates"] = date_info["corrected"]
                elif dates := analysis_result["core_info"].get("dates"):
                    conversation_state["travel_dates"] = dates
            
            if duration := analysis_result["core_info"].get("duration"):
                conversation_state["duration"] = duration
                conversation_state["confirmed_info"].add("travel_dates")
            
            if preferences := analysis_result["core_info"].get("preferences"):
                current_preferences = set(conversation_state.get("preferences", []))
                current_preferences.update(preferences)
                conversation_state["preferences"] = list(current_preferences)
            
            conversation_state["last_topic"] = analysis_result["context"]["current_topic"]
            conversation_state["context_keywords"].update(
                analysis_result["context"]["user_interests"]
            )
            
            required_info = set(analysis_result["next_steps"]["required_info"])
            conversation_state["pending_questions"] = list(
                required_info - conversation_state["confirmed_info"]
            )
            
            conversation_state["interaction_history"].append({
                "timestamp": datetime.now().isoformat(),
                "topic": analysis_result["context"]["current_topic"],
                "collected_info": list(required_info & conversation_state["confirmed_info"])
            })
            
        except json.JSONDecodeError:
            print("Warning: Failed to parse analysis result")
        
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
        memory_size = state.get("memory_size", 10)
        
        has_destination = bool(conversation_state.get("destination"))
        has_dates = bool(conversation_state.get("travel_dates"))
        has_preferences = bool(conversation_state.get("preferences"))
        
        recent_messages = messages[-memory_size:] if len(messages) >= 3 else messages
        plan_keywords = ["계획", "일정", "스케줄", "플랜", "짜줘"]
        
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                content = msg.content.lower()
                if any(keyword in content for keyword in plan_keywords):
                    if has_destination and has_dates and has_preferences:
                        return str(ConversationState.GENERATE_PLAN)
                
                if ("그대로" in content or "이대로" in content) and any(keyword in content for keyword in ["계획", "진행", "시작"]):
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