from typing import Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class TravelPlan(BaseModel):
    """여행 계획"""
    response: str = Field(..., description="응답 메시지")
    has_plan: bool = Field(..., description="계획 생성 여부")
    plan: dict = Field(default_factory=dict, description="생성된 계획")

class ChatMessage(BaseModel):
    """채팅 메시지"""
    role: str = Field(..., description="메시지 작성자 역할 (system, user, assistant)")
    content: str = Field(..., description="메시지 내용")
    timestamp: Optional[Union[datetime, str]] = Field(default_factory=lambda: datetime.now().isoformat(), description="메시지 작성 시간") 