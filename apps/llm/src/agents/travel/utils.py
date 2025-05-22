from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage, SystemMessage
import json

def select_next_question(pending_questions: List[str], last_topic: str, interaction_history: List[Dict]) -> Optional[str]:
    """다음에 물어볼 질문 선택"""
    if not pending_questions:
        return None
    
    question_priority = [
        "destination",
        "travel_dates",
        "preferences",
        "accommodation",
        "transportation"
    ]
    
    for priority in question_priority:
        for question in pending_questions:
            if priority in question.lower():
                return question
    
    return pending_questions[0]

def create_context_message(conversation_state: Dict) -> Optional[SystemMessage]:
    """현재 대화 컨텍스트를 바탕으로 시스템 메시지 생성"""
    if not conversation_state:
        return None
        
    context_parts = []
    if destination := conversation_state.get("destination"):
        context_parts.append(f"목적지: {destination}")
    if travel_dates := conversation_state.get("travel_dates"):
        context_parts.append(f"여행 기간: {travel_dates}")
    elif duration := conversation_state.get("duration"):
        context_parts.append(f"여행 기간: {duration}박 {duration+1}일")
    if preferences := conversation_state.get("preferences"):
        context_parts.append(f"선호도: {', '.join(preferences)}")
        
    if context_parts:
        context_msg = """여행 계획을 도와드리는 AI 어시스턴트입니다.
        현재까지 파악된 정보:
        {}
        
        이 정보를 바탕으로 대화를 이어가겠습니다.""".format("\n".join(context_parts))
        
        return SystemMessage(content=context_msg)
    
    return None

def analyze_preferences(llm, messages: List[BaseMessage], memory_size: int = 10) -> List[str]:
    """LLM을 사용하여 메시지에서 선호도 분석"""
    if not messages:
        return []
    
    recent_messages = messages[-memory_size:]
    
    analysis_prompt = SystemMessage(content="""사용자의 메시지에서 여행 선호도를 분석해주세요.

    분석해야 할 카테고리:
    1. 동반자 유형 (예: 가족여행, 커플여행, 친구들과 여행 등)
    2. 선호하는 활동 (예: 관광, 휴식, 체험, 쇼핑 등)
    3. 선호하는 장소 (예: 자연/아웃도어, 도시, 문화유적, 해변 등)
    4. 식사 선호도 (예: 현지식, 맛집탐방, 카페 등)
    5. 숙박 선호도 (예: 호텔, 리조트, 게스트하우스 등)
    6. 이동수단 (예: 대중교통, 렌터카, 도보 등)
    7. 여행 스타일 (예: 여유로운, 활동적인, 계획적인, 즉흥적인 등)
    
    응답 형식:
    {
        "preferences": [
            {
                "category": "카테고리명",
                "value": "선호도",
                "confidence": 0.0-1.0,  // 신뢰도
                "evidence": "근거가 되는 사용자 발화"
            }
        ]
    }
    
    주의사항:
    1. 명확한 근거가 있는 선호도만 포함
    2. 추측이나 가정은 하지 않음
    3. 신뢰도는 문맥과 표현의 명확성을 기준으로 판단""")
    
    analysis_messages = [analysis_prompt, *recent_messages]
    response = llm.invoke(analysis_messages)
    
    try:
        result = json.loads(response.content)
        
        preferences = []
        for pref in result.get("preferences", []):
            if pref.get("confidence", 0) >= 0.7:
                preference_str = f"{pref['category']}: {pref['value']}"
                preferences.append(preference_str)
        
        return preferences
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Failed to parse preferences analysis - {str(e)}")
        return [] 