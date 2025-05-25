from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import json
import asyncio
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

from ..models.travel import ChatMessage
from ..agents.travel.travel_agent import TravelPlannerAgent
from ..utils.llm import get_llm, get_available_models

class TravelPlanRequest(BaseModel):
    messages: List[ChatMessage]
    user_preferences: Optional[Dict] = None
    current_plan: Optional[Dict] = None
    llm_config: Optional[Dict] = None

class ModelConfig(BaseModel):
    provider: str
    model: str

router = APIRouter(prefix="/travel", tags=["travel"])

current_model_config = {"provider": "openai", "model": "gpt-3.5-turbo-1106"}

def get_current_agent():
    """현재 모델 설정을 사용하여 TravelPlannerAgent 인스턴스 반환"""
    global current_model_config
    
    try:
        llm = get_llm(
            provider=current_model_config["provider"], 
            model=current_model_config["model"]
        )
        return TravelPlannerAgent(llm=llm)
    except ValueError as e:
        available_models = get_available_models()
        for provider, models in available_models.items():
            if models:
                try:
                    llm = get_llm(provider=provider, model=models[0])
                    current_model_config = {"provider": provider, "model": models[0]}
                    return TravelPlannerAgent(llm=llm)
                except ValueError:
                    continue
        raise HTTPException(
            status_code=500,
            detail="사용 가능한 AI 모델이 없습니다. API 키를 확인해주세요."
        )

@router.get("/models")
async def get_models():
    """사용 가능한 모델 목록 반환"""
    return get_available_models()

@router.post("/models/config")
async def set_model_config(config: ModelConfig):
    """모델 설정 변경"""
    global current_model_config
    available_models = get_available_models()
    
    if config.provider not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {config.provider}. 사용 가능한 제공업체: {list(available_models.keys())}"
        )
    
    if config.model not in available_models[config.provider]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {config.model} for provider: {config.provider}"
        )

@router.get("/models/config")
async def get_model_config():
    """현재 모델 설정 반환"""
    return current_model_config

async def stream_response(result: dict):
    """스트리밍 응답 생성기"""
    response_text = result.get("response", "")
    chunk_size = 50
    
    yield f"data: {json.dumps({'status': 'start', 'message': '여행 계획 생성을 시작합니다.'})}\n\n"
    await asyncio.sleep(0.01)
    
    progress_states = [
        ("분석", "여행 선호도를 분석하고 있습니다..."),
        ("검색", "최적의 여행지를 검색하고 있습니다..."),
        ("계획", "상세 일정을 계획하고 있습니다..."),
        ("최적화", "일정을 최적화하고 있습니다..."),
        ("마무리", "최종 계획을 정리하고 있습니다...")
    ]
    
    total_chunks = len(response_text) // chunk_size + 1
    chunks_per_state = total_chunks // len(progress_states)
    
    for i, (state, message) in enumerate(progress_states):
        yield f"data: {json.dumps({'status': 'progress', 'state': state, 'message': message, 'progress': (i+1)/len(progress_states)})}\n\n"
        
        chunk_start = i * chunks_per_state * chunk_size
        chunk_end = (i + 1) * chunks_per_state * chunk_size
        
        current_text = response_text[chunk_start:chunk_end]
        for j in range(0, len(current_text), chunk_size):
            chunk = current_text[j:j + chunk_size]
            yield f"data: {json.dumps({'response': chunk})}\n\n"
            await asyncio.sleep(0.02)
    
    remaining_text = response_text[chunk_end:]
    if remaining_text:
        for i in range(0, len(remaining_text), chunk_size):
            chunk = remaining_text[i:i + chunk_size]
            yield f"data: {json.dumps({'response': chunk})}\n\n"
            await asyncio.sleep(0.02)
    
    if result.get("has_plan"):
        plan_data = result.get("plan", {})
        
        yield f"data: {json.dumps({'has_plan': True, 'plan': plan_data})}\n\n"
    
    yield f"data: {json.dumps({'status': 'complete', 'message': '여행 계획이 완성되었습니다.'})}\n\n"

@router.post("/plan")
async def create_travel_plan(request: TravelPlanRequest):
    """채팅 기반으로 여행 계획 생성 (스트리밍)"""
    try:
        message_dicts = [msg.model_dump() for msg in request.messages]
        
        if request.user_preferences:
            preferences_msg = {
                "role": "system",
                "content": f"""사용자의 여행 선호도 정보:
                - 여행 기간: {request.user_preferences.get('travel_dates', {}).get('start')} ~ {request.user_preferences.get('travel_dates', {}).get('end')}
                - 여행지: {request.user_preferences.get('destination', '미정')}
                - 예산: {request.user_preferences.get('budget', '미정')}만원
                - 선호 활동: {', '.join(request.user_preferences.get('preferences', {}).get('activities', []))}
                - 숙소 유형: {request.user_preferences.get('preferences', {}).get('accommodation', '미정')}
                - 이동수단: {request.user_preferences.get('preferences', {}).get('transport', '미정')}
                
                특별 요청사항: {request.user_preferences.get('preferences', {}).get('special_requests', '없음')}
                
                위 정보를 참고하여 여행 계획을 수립해주세요.""",
                "timestamp": datetime.now().isoformat()
            }
            message_dicts.insert(0, preferences_msg)
        
        agent = get_current_agent()
        
        result = agent.chat(
            message_dicts, 
            user_preferences=request.user_preferences,
            current_plan=request.current_plan
        )
        
        return StreamingResponse(
            stream_response(result),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "travel_plan_creation_failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )