import re
from typing import Optional, Dict
from datetime import datetime
from langchain_core.messages import SystemMessage
import json

def parse_user_event_selection(message: str) -> Optional[int]:
    """사용자 메시지에서 이벤트 번호 추출"""
    number_pattern = r'(\d+)\s*번'
    match = re.search(number_pattern, message)
    if match:
        return int(match.group(1))
    
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
    
    digits = re.findall(r'\b(\d+)\b', message)
    if digits:
        return int(digits[0])
    
    return None

def understand_modification_request(message: str, llm, existing_event: Dict = None) -> Optional[Dict]:
    """LLM을 사용하여 사용자 메시지에서 수정 내용 추출"""
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