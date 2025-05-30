from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.store.memory import InMemoryStore

from .types import ConversationState, TravelPlannerState
from .state_handlers import (
    check_guardrail,
    understand_request, 
    determine_next_step, 
    ask_destination, 
    collect_details, 
    generate_plan, 
    refine_plan,
    register_calendar,
    view_calendar,
    modify_calendar,
    delete_calendar
)

class TravelPlannerAgent:
    """대화형 여행 계획 에이전트"""
    
    CONVERSATION_MEMORY_SIZE = 10
    
    def __init__(self, llm):
        self.llm = llm
        self.store = InMemoryStore()
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(
            store=self.store
        )
    
    def _create_workflow(self) -> StateGraph:
        """대화 워크플로우 생성"""
        workflow = StateGraph(TravelPlannerState)
        
        workflow.add_node(str(ConversationState.CHECK_GUARDRAIL), 
                         lambda state: check_guardrail(self.llm, state))
        workflow.add_node(str(ConversationState.UNDERSTAND_REQUEST), 
                         lambda state: understand_request(self.llm, state))
        workflow.add_node(str(ConversationState.GENERATE_PLAN), 
                         lambda state: generate_plan(self.llm, state))
        workflow.add_node(str(ConversationState.REFINE_PLAN), 
                         lambda state: refine_plan(self.llm, state))
        workflow.add_node(str(ConversationState.ASK_DESTINATION), 
                         lambda state: ask_destination(self.llm, state))
        workflow.add_node(str(ConversationState.COLLECT_DETAILS), 
                         lambda state: collect_details(self.llm, state))
        workflow.add_node(str(ConversationState.REGISTER_CALENDAR), 
                         lambda state: register_calendar(self.llm, state))
        workflow.add_node(str(ConversationState.VIEW_CALENDAR), 
                         lambda state: view_calendar(self.llm, state))
        workflow.add_node(str(ConversationState.MODIFY_CALENDAR), 
                         lambda state: modify_calendar(self.llm, state))
        workflow.add_node(str(ConversationState.DELETE_CALENDAR), 
                         lambda state: delete_calendar(self.llm, state))
        
        workflow.set_entry_point(str(ConversationState.CHECK_GUARDRAIL))

        workflow.add_conditional_edges(
            str(ConversationState.CHECK_GUARDRAIL),
            lambda state: state.get("current_step", str(ConversationState.END)),
            {
                str(ConversationState.UNDERSTAND_REQUEST): str(ConversationState.UNDERSTAND_REQUEST),
                str(ConversationState.END): END
            }
        )

        workflow.add_conditional_edges(
            str(ConversationState.UNDERSTAND_REQUEST),
            lambda state: determine_next_step({**state, "llm": self.llm}),
            {
                str(ConversationState.ASK_DESTINATION): str(ConversationState.ASK_DESTINATION),
                str(ConversationState.COLLECT_DETAILS): str(ConversationState.COLLECT_DETAILS),
                str(ConversationState.GENERATE_PLAN): str(ConversationState.GENERATE_PLAN),
                str(ConversationState.REFINE_PLAN): str(ConversationState.REFINE_PLAN),
                str(ConversationState.REGISTER_CALENDAR): str(ConversationState.REGISTER_CALENDAR),
                str(ConversationState.VIEW_CALENDAR): str(ConversationState.VIEW_CALENDAR),
                str(ConversationState.MODIFY_CALENDAR): str(ConversationState.MODIFY_CALENDAR),
                str(ConversationState.DELETE_CALENDAR): str(ConversationState.DELETE_CALENDAR),
                str(ConversationState.END): END
            }
        )
        
        workflow.add_edge(str(ConversationState.ASK_DESTINATION), END)
        workflow.add_edge(str(ConversationState.COLLECT_DETAILS), END)
        workflow.add_edge(str(ConversationState.GENERATE_PLAN), END)
        workflow.add_edge(str(ConversationState.REFINE_PLAN), END)
        workflow.add_edge(str(ConversationState.REGISTER_CALENDAR), END)
        workflow.add_edge(str(ConversationState.VIEW_CALENDAR), END)
        
        workflow.add_conditional_edges(
            str(ConversationState.MODIFY_CALENDAR),
            lambda state: self._determine_calendar_next_step(state, "modification"),
            {
                str(ConversationState.MODIFY_CALENDAR): str(ConversationState.MODIFY_CALENDAR),
                str(ConversationState.END): END
            }
        )
        
        workflow.add_conditional_edges(
            str(ConversationState.DELETE_CALENDAR),
            lambda state: self._determine_calendar_next_step(state, "deletion"),
            {
                str(ConversationState.DELETE_CALENDAR): str(ConversationState.DELETE_CALENDAR),
                str(ConversationState.END): END
            }
        )
        
        return workflow

    def _determine_calendar_next_step(self, state: Dict, operation_type: str) -> str:
        """캘린더 작업(수정/삭제)의 다음 단계 결정"""
        calendar_data = state.get("calendar_data", {})
        
        if operation_type == "modification":
            step = calendar_data.get("modification_step", "")
            if step in ["completed", "error"]:
                return str(ConversationState.END)
            else:
                return str(ConversationState.MODIFY_CALENDAR)
                
        elif operation_type == "deletion":
            step = calendar_data.get("deletion_step", "")
            if step in ["completed", "cancelled", "error"]:
                return str(ConversationState.END)
            else:
                return str(ConversationState.DELETE_CALENDAR)
        
        return str(ConversationState.END)

    def chat(self, messages: List[dict], user_preferences: Optional[Dict] = None, current_plan: Optional[Dict] = None) -> dict:
        """Run the travel planner workflow"""
        try:
            base_messages = []
            
            if user_preferences:
                preferences_msg = """사용자의 여행 선호도 정보:
                - 여행 기간: {start} ~ {end}
                - 여행지: {destination}
                - 선호 활동: {activities}
                - 숙소 유형: {accommodation}
                - 이동수단: {transport}
                - 특별 요청사항: {special_requests}
                """.format(
                    start=user_preferences.get("travel_dates", {}).get("start", "미정"),
                    end=user_preferences.get("travel_dates", {}).get("end", "미정"),
                    destination=user_preferences.get("destination", "미정"),
                    activities=", ".join(user_preferences.get("preferences", {}).get("activities", [])),
                    accommodation=user_preferences.get("preferences", {}).get("accommodation", "미정"),
                    transport=user_preferences.get("preferences", {}).get("transport", "미정"),
                    special_requests=user_preferences.get("preferences", {}).get("special_requests", "없음")
                )
                base_messages.append(SystemMessage(content=preferences_msg))
            
            for msg in messages:
                if msg["role"] == "user":
                    base_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    base_messages.append(AIMessage(content=msg["content"]))
            
            plan_data = {}
            if current_plan:
                # JSON 형식 계획 처리
                if current_plan.get("plan_data"):
                    plan_data = {
                        "generated_at": current_plan.get("generated_at", "client"),
                        "plan_data": current_plan.get("plan_data"),
                        "collected_info": current_plan.get("collected_info", ""),
                        "format": "json"
                    }
                # 텍스트 형식 계획 처리
                elif current_plan.get("content"):
                    plan_data = {
                        "generated_at": current_plan.get("generated_at", "client"),
                        "content": current_plan.get("content"),
                        "collected_info": current_plan.get("collected_info", ""),
                        "format": "text"
                    }
            
            # conversation_state를 메시지 히스토리와 user_preferences에서 복원
            conversation_state = {}
            if user_preferences:
                # user_preferences에서 기본 정보 추출
                travel_dates = user_preferences.get("travel_dates", {})
                if travel_dates.get("start") and travel_dates.get("end"):
                    conversation_state["travel_dates"] = f"{travel_dates['start']} ~ {travel_dates['end']}"
                
                conversation_state["destination"] = user_preferences.get("destination")
                
                preferences = user_preferences.get("preferences", {})
                activities = preferences.get("activities", [])
                if activities:
                    conversation_state["preferences"] = activities
            
            initial_state = {
                "messages": base_messages,
                "current_step": str(ConversationState.CHECK_GUARDRAIL),
                "plan_data": plan_data,
                "required_info": {},
                "conversation_state": conversation_state,
                "calendar_data": {},
                "memory_size": self.CONVERSATION_MEMORY_SIZE
            }

            result = self.app.invoke(initial_state)
            
            return {
                "response": result["messages"][-1].content if result.get("messages") else "죄송합니다. 응답을 생성하는 중 문제가 발생했습니다.",
                "has_plan": bool(result.get("plan_data")),
                "plan": result.get("plan_data", {})
            }
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return {
                "response": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.",
                "has_plan": False,
                "plan": {}
            } 