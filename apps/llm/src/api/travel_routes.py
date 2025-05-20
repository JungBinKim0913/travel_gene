from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import json
import asyncio

from ..models.travel import ChatMessage, TravelPlan
from ..agents.travel_agent import TravelPlannerAgent
from ..utils.llm import get_llm

router = APIRouter(prefix="/travel", tags=["travel"])
agent = TravelPlannerAgent(llm=get_llm())

async def stream_response(result: dict):
    """스트리밍 응답 생성기"""
    response_text = result.get("response", "")
    
    for char in response_text:
        yield f"data: {json.dumps({'response': char})}\n\n"
        await asyncio.sleep(0.01)
    
    if result.get("has_plan"):
        yield f"data: {json.dumps({'has_plan': True, 'plan': result.get('plan', {})})}\n\n"

@router.post("/plan")
async def create_travel_plan(messages: List[ChatMessage]):
    """채팅 기반으로 여행 계획 생성 (스트리밍)"""
    try:
        message_dicts = [msg.model_dump() for msg in messages]
        result = agent.chat(message_dicts)
        
        return StreamingResponse(
            stream_response(result),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_agent(message: ChatMessage):
    """여행 계획을 위한 대화형 인터페이스"""
    try:
        response = ChatMessage(
            role="assistant",
            content="아직 구현되지 않았습니다."
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 