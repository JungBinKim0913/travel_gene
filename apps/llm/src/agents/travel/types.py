from typing import TypedDict, List
from langchain_core.messages import BaseMessage
from enum import Enum, auto

class ConversationState(Enum):
    UNDERSTAND_REQUEST = auto()
    ASK_DESTINATION = auto()
    COLLECT_DETAILS = auto()
    GENERATE_PLAN = auto()
    REFINE_PLAN = auto()
    REGISTER_CALENDAR = auto()
    END = auto()

    def __str__(self):
        return self.name

class TravelPlannerState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
    plan_data: dict
    required_info: dict
    conversation_state: dict
    calendar_data: dict 