from fastapi import APIRouter, HTTPException
from typing import List

from ..models.travel import ChatMessage, TravelPlan
from ..agents.travel_agent import TravelPlannerAgent
from ..utils.llm import get_llm

router = APIRouter(prefix="/travel", tags=["travel"])
agent = TravelPlannerAgent(llm=get_llm())

@router.post("/plan", response_model=TravelPlan)
async def create_travel_plan(messages: List[ChatMessage]):
    """채팅 기반으로 여행 계획 생성"""
    try:
        message_dicts = [msg.model_dump() for msg in messages]
        
        result = agent.chat(message_dicts)
        
        return TravelPlan(
            response=result.get("response", ""),
            has_plan=result.get("has_plan", False),
            plan=result.get("plan", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatMessage)
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