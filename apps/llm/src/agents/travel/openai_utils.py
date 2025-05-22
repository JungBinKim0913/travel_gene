import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def is_openai_model(llm: Any) -> bool:
    """LLM이 OpenAI 모델인지 확인합니다."""
    llm_type = str(type(llm)).lower()
    return "openai" in llm_type or "chatgpt" in llm_type or "gpt" in llm_type

def extract_json_from_response(response: str) -> Dict:
    """응답에서 JSON 부분을 추출합니다."""
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > 0:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        return {}
    except:
        return {}

def request_json_response(
    messages: List[Dict], 
    json_schema: Dict,
    model: str = "gpt-4-1106-preview"
) -> Dict:
    """
    OpenAI의 Structured Outputs 기능을 사용하여 JSON 형식의 응답을 강제합니다.
    
    Args:
        messages: OpenAI 형식의 메시지 리스트
        json_schema: 응답의 JSON 스키마 (프롬프트에 포함하여 안내)
        model: 사용할 OpenAI 모델
        
    Returns:
        Dict: JSON 응답
    """
    try:
        has_system_message = False
        for msg in messages:
            if msg.get("role") == "system":
                has_system_message = True
                msg["content"] = f"{msg['content']}\n\n응답은 반드시 다음 JSON 스키마를 따라야 합니다:\n{json.dumps(json_schema, ensure_ascii=False)}"
                break
        
        if not has_system_message:
            messages.insert(0, {
                "role": "system",
                "content": f"응답은 반드시 다음 JSON 스키마를 따라야 합니다:\n{json.dumps(json_schema, ensure_ascii=False)}"
            })
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {}

def convert_langchain_messages_to_openai_format(messages: List) -> List[Dict]:
    """LangChain 메시지 형식을 OpenAI 형식으로 변환합니다."""
    openai_messages = []
    
    for msg in messages:
        if isinstance(msg, SystemMessage):
            openai_messages.append({"role": "system", "content": msg.content})
        elif isinstance(msg, HumanMessage):
            openai_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            openai_messages.append({"role": "assistant", "content": msg.content})
    
    return openai_messages

def analyze_conversation_with_json_structure(
    llm: Any,
    messages: List,
    current_year: int
) -> Dict:
    """
    대화를 분석하고 JSON 구조로 결과를 반환합니다.
    LLM이 OpenAI 모델인 경우 Structured Outputs 기능을 사용합니다.
    
    Args:
        llm: 언어 모델
        messages: 분석할 메시지 리스트
        current_year: 현재 연도
        
    Returns:
        Dict: 분석 결과 (JSON 형식)
    """
    json_schema = {
        "type": "object",
        "properties": {
            "core_info": {
                "type": "object",
                "properties": {
                    "destination": {"type": ["string", "null"]},
                    "dates": {"type": ["string", "null"]},
                    "duration": {"type": ["integer", "null"]},
                    "date_validation": {
                        "type": "object",
                        "properties": {
                            "is_valid": {"type": "boolean"},
                            "original": {"type": "string"},
                            "corrected": {"type": "string"}
                        }
                    },
                    "preferences": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "context": {
                "type": "object",
                "properties": {
                    "current_topic": {"type": "string"},
                    "related_to_previous": {"type": "boolean"},
                    "user_interests": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "next_steps": {
                "type": "object",
                "properties": {
                    "required_info": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "suggested_questions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    }
    
    system_prompt = f"""당신은 여행 대화 분석 전문가입니다. 주어진 대화 내용을 분석하여 정확히 아래 JSON 형식으로만 응답해야 합니다.

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

    응답은 반드시 다음 JSON 스키마를 따라야 합니다:
    {json.dumps(json_schema, ensure_ascii=False)}
    
    날짜 처리 예시:
    1. "다음 주 토요일" -> "{current_year}년 MM월 DD일 (토)"
    2. "크리스마스" -> "{current_year}년 12월 25일 (수)"
    3. "6월 7일" -> "{current_year}년 6월 7일 (금)"
    
    잘못된 날짜/요일 조합 예시:
    입력: "{current_year}년 6월 7일 (토)" -> 수정: "{current_year}년 6월 7일 (금)" (실제 요일로 수정)"""
    
    analysis_messages = [SystemMessage(content=system_prompt)]
    analysis_messages.extend(messages)
    
    if is_openai_model(llm):
        try:
            openai_messages = convert_langchain_messages_to_openai_format(analysis_messages)
            
            return request_json_response(openai_messages, json_schema)
        except Exception as e:
            print(f"Error using OpenAI structured output: {str(e)}")
    
    try:
        response = llm.invoke(analysis_messages)
        content = response.content
        
        return extract_json_from_response(content)
    except Exception as e:
        print(f"Error in analyze_conversation: {str(e)}")
        return {} 