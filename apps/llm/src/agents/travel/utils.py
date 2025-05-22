from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage, SystemMessage
from datetime import datetime
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

def analyze_user_intent(llm, message: str, has_plan: bool, previous_ai_message: str = None) -> Dict:
    """LLM을 사용하여 사용자 메시지의 의도 분석"""
    plan_status = "이미 생성되었습니다" if has_plan else "아직 생성되지 않았습니다"
    
    system_prompt = f"""사용자의 메시지에서 의도를 분석해주세요. 현재 여행 계획 에이전트와 대화 중입니다.
    여행 계획이 {plan_status}.
    
    다음 중 가장 일치하는 의도를 식별하고, 해당 의도의 신뢰도(0.0~1.0)를 응답해주세요:
    
    1. 여행 계획 생성 요청: 사용자가 새로운 여행 계획을 만들어달라고 요청
    2. 캘린더 등록 요청: 생성된 여행 계획을 Google Calendar에 등록해달라고 요청
    3. 계획 세부정보 문의: 여행 계획의 특정 부분에 대해 질문
    4. 계획 수정 요청: 생성된 계획의 일부를 변경해달라고 요청
    5. 긍정 응답: 이전 질문이나 제안에 대한 긍정적인 답변 (예: "네", "좋아요", "그래요")
    6. 부정 응답: 이전 질문이나 제안에 대한 부정적인 답변 (예: "아니요", "싫어요")
    7. 일반 대화: 특별한 의도 없이 일반적인 대화 진행
    
    응답은 정확한 JSON 형식으로 제공해주세요. 다음 필드가 포함되어야 합니다:
    - primary_intent: 위 목록 중 가장 적합한 의도
    - confidence: 0.0에서 1.0 사이의 신뢰도 점수
    - keywords_detected: 탐지된 핵심 키워드들의 배열
    - requires_plan: 해당 의도가 기존 계획을 필요로 하는지 여부 (true/false)
    - context_analysis: 간단한 메시지 문맥 분석
    - is_affirmative_to_previous: 이전 제안에 대한 긍정 응답인지 여부 (true/false)
    """
    
    messages = [
        SystemMessage(content=system_prompt),
    ]
    
    if previous_ai_message:
        messages.append(SystemMessage(content=f"직전 AI 메시지: {previous_ai_message}"))
    
    messages.append(SystemMessage(content=f"분석할 사용자 메시지: {message}"))
    
    response = llm.invoke(messages)
    
    try:
        result = json.loads(response.content)
        return result
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Failed to parse intent analysis - {str(e)}")
        return {
            "primary_intent": "일반 대화",
            "confidence": 0.5,
            "keywords_detected": [],
            "requires_plan": False,
            "context_analysis": "분석 실패",
            "is_affirmative_to_previous": False
        } 