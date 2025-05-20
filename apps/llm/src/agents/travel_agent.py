from typing import TypedDict, List, Dict
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.schema import SystemMessage

from ..utils.parsers import parse_json_response

class TravelPlannerState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
    plan_data: dict
    required_info: dict

class TravelPlannerAgent:
    """대화형 여행 계획 에이전트"""
    
    def __init__(self, llm):
        self.llm = llm
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(
            checkpointer=self.checkpointer,
            store=self.store
        )
    
    def _create_workflow(self) -> StateGraph:
        """대화 워크플로우 생성"""
        workflow = StateGraph(TravelPlannerState)
        
        # 노드 정의
        workflow.add_node("understand_request", self._understand_request)
        workflow.add_node("check_required_info", self._check_required_info)
        workflow.add_node("request_info", self._request_info)
        workflow.add_node("process_user_response", self._process_user_response)
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("refine_plan", self._refine_plan)
        
        # 시작점 설정
        workflow.set_entry_point("understand_request")

        # 엣지 정의
        workflow.add_conditional_edges(
            "understand_request",
            self._should_check_info,
            {
                "check": "check_required_info",
                "generate": "generate_plan",
                "refine": "refine_plan",
                "continue": "process_user_response"
            }
        )
        
        workflow.add_conditional_edges(
            "check_required_info",
            self._should_request_info,
            {
                "request": "request_info",
                "generate": "generate_plan"
            }
        )
        
        workflow.add_edge("request_info", END)
        
        workflow.add_conditional_edges(
            "process_user_response",
            self._should_check_info,
            {
                "check": "check_required_info",
                "generate": "generate_plan",
                "refine": "refine_plan",
                "continue": "process_user_response"
            }
        )
        
        workflow.add_edge("generate_plan", "refine_plan")
        workflow.add_edge("refine_plan", END)
        
        return workflow
    
    def _understand_request(self, state: Dict) -> Dict:
        """Understand the user's travel request"""
        messages = state.get("messages", [])
        current_step = state.get("current_step", "")
        plan_data = state.get("plan_data", {})

        # 시스템 메시지 추가
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages.insert(0, SystemMessage(content="""여행 계획을 도와주는 AI 어시스턴트입니다. 
            사용자의 요구사항을 이해하고 적절한 여행 계획을 제안해드리겠습니다."""))

        response = self.llm.invoke(messages)
        messages.append(response)
        
        # 이전 상태를 유지하면서 업데이트
        return {
            **state,  # 기존 상태 보존
            "messages": messages,
            "current_step": "understand_request",
            "plan_data": plan_data
        }

    def _should_check_info(self, state: Dict) -> str:
        """다음 단계 결정"""
        messages = state.get("messages", [])
        last_msg = messages[-1].content.lower() if messages else ""
        
        if "modify" in last_msg or "수정" in last_msg:
            return "refine"
        elif any(keyword in last_msg for keyword in ["여행", "계획", "travel", "plan"]):
            return "check"
        else:
            return "continue"

    def _check_required_info(self, state: Dict) -> Dict:
        """필요한 정보 체크"""
        messages = state.get("messages", [])
        required_info = state.get("required_info", {})
        
        # 시스템 메시지로 정보 체크 지시
        check_prompt = SystemMessage(content="""사용자의 여행 계획을 위해 제공된 정보를 분석해주세요.
        다음 정보들에 대해 평가해주세요:
        
        1. 여행 기간
        2. 여행지
        3. 예산
        4. 선호하는 활동이나 제약사항
        
        각 항목에 대해 다음과 같이 평가해주세요:
        - "충분": 정보가 명확하고 충분함
        - "불충분": 정보가 있지만 더 구체적인 내용이 필요함
        - "없음": 정보가 전혀 없음
        
        JSON 형식으로 응답해주세요. 예시:
        {
            "duration": {
                "status": "불충분",
                "current": "여행을 가고 싶다고만 언급",
                "needed": "정확한 여행 기간(몇박몇일)"
            },
            "destination": {
                "status": "충분",
                "current": "제주도",
                "needed": null
            }
        }""")
        
        messages.append(check_prompt)
        response = self.llm.invoke(messages)
        messages.append(response)
        
        # 응답에서 정보 상태 추출
        try:
            info_status = parse_json_response(response.content)
            required_info = info_status
        except:
            required_info = {}
        
        return {
            **state,
            "messages": messages,
            "current_step": "check_required_info",
            "required_info": required_info
        }

    def _should_request_info(self, state: Dict) -> str:
        """정보 요청 필요 여부 확인"""
        required_info = state.get("required_info", {})
        
        # 불충분하거나 없는 정보 확인
        missing_info = [
            k for k, v in required_info.items() 
            if isinstance(v, dict) and v.get("status") in ["불충분", "없음"]
        ]
        return "request" if missing_info else "generate"

    def _request_info(self, state: Dict) -> Dict:
        """부족한 정보 요청"""
        messages = state.get("messages", [])
        required_info = state.get("required_info", {})
        
        # 불충분하거나 없는 정보 수집
        missing_info = {
            k: v for k, v in required_info.items()
            if isinstance(v, dict) and v.get("status") in ["불충분", "없음"]
        }
        
        # 정보 요청 메시지 생성
        request_msg = "여행 계획을 세우기 위해 몇 가지 정보가 더 필요합니다:\n\n"
        
        for key, info in missing_info.items():
            current = info.get("current", "아직 언급되지 않음")
            needed = info.get("needed", "구체적인 정보")
            
            if key == "duration":
                field_name = "여행 기간"
            elif key == "destination":
                field_name = "여행지"
            elif key == "budget":
                field_name = "예산"
            elif key == "preferences":
                field_name = "선호사항"
            else:
                field_name = key
                
            request_msg += f"- {field_name}:\n"
            request_msg += f"  현재 정보: {current}\n"
            request_msg += f"  필요한 정보: {needed}\n\n"
        
        messages.append(AIMessage(content=request_msg.strip()))
        
        return {
            **state,
            "messages": messages,
            "current_step": "request_info",
            "required_info": required_info
        }

    def _process_user_response(self, state: Dict) -> Dict:
        """사용자 응답 처리"""
        messages = state.get("messages", [])
        required_info = state.get("required_info", {})
        
        analyze_prompt = SystemMessage(content="""사용자의 응답을 분석하여 제공된 정보를 추출해주세요.
        다음 정보들이 포함되어 있는지 확인해주세요:
        - 여행 기간
        - 여행지
        - 예산
        - 선호하는 활동이나 제약사항
        
        발견된 정보를 JSON 형식으로 응답해주세요. 예시:
        {
            "duration": {
                "found": true,
                "value": "3박 4일",
                "confidence": "high"
            },
            "destination": {
                "found": true,
                "value": "제주도",
                "confidence": "high"
            }
        }""")
        
        messages.append(analyze_prompt)
        response = self.llm.invoke(messages)
        messages.append(response)
        
        try:
            analysis = parse_json_response(response.content)
            
            for key, info in analysis.items():
                if info.get("found") and info.get("confidence") in ["high", "medium"]:
                    if key in required_info:
                        required_info[key].update({
                            "status": "충분" if info.get("confidence") == "high" else "불충분",
                            "current": info.get("value"),
                            "needed": None if info.get("confidence") == "high" else "더 구체적인 정보"
                        })
        except:
            pass
        
        return {
            **state,
            "messages": messages,
            "current_step": "process_user_response",
            "required_info": required_info
        }

    def _generate_plan(self, state: Dict) -> Dict:
        """Generate initial travel plan"""
        messages = state.get("messages", [])
        current_step = state.get("current_step", "")
        plan_data = state.get("plan_data", {})

        messages.append(SystemMessage(content="""다음 형식으로 여행 계획을 생성해주세요:
        1. 여행 기간
        2. 주요 방문지
        3. 일자별 세부 일정
        4. 예상 비용"""))

        response = self.llm.invoke(messages)
        messages.append(response)
        
        plan_data = {
            "generated_at": "generate_plan",
            "content": response.content
        }
        
        return {
            **state,
            "messages": messages,
            "current_step": "generate_plan",
            "plan_data": plan_data
        }

    def _refine_plan(self, state: Dict) -> Dict:
        """Refine the travel plan"""
        messages = state.get("messages", [])
        plan_data = state.get("plan_data", {})

        messages.append(SystemMessage(content="""기존 계획을 검토하고 사용자의 피드백을 반영하여 수정해주세요.
        변경된 부분을 명확히 표시해주세요."""))

        response = self.llm.invoke(messages)
        messages.append(response)
        
        new_plan_data = {
            "generated_at": "refine_plan",
            "content": response.content,
            "previous_plan": plan_data.get("content", "")
        }
        
        return {
            **state,
            "messages": messages,
            "current_step": "refine_plan",
            "plan_data": new_plan_data
        }

    def chat(self, messages: List[dict]) -> dict:
        """Run the travel planner workflow"""
        # TODO: 클라이언트에서 넘어온 thread_id 사용
        import uuid
        thread_id = str(uuid.uuid4())
        
        config = {
            "configurable": {
                "thread_id": thread_id,
                "session_id": "travel_planner"
            },
            "metadata": {
                "conversation_id": thread_id
            }
        }
        
        base_messages = []
        for msg in messages:
            if msg["role"] == "user":
                base_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                base_messages.append(AIMessage(content=msg["content"]))
        
        initial_state = {
            "messages": base_messages,
            "current_step": "process_user_response" if len(base_messages) > 0 else "understand_request",
            "plan_data": {},
            "required_info": {}
        }

        result = self.app.invoke(initial_state, config=config)
        
        return {
            "response": result["messages"][-1].content if result["messages"] else "",
            "has_plan": bool(result["plan_data"]),
            "plan": result["plan_data"],
            "needs_info": bool([k for k, v in result.get("required_info", {}).items() 
                              if isinstance(v, dict) and v.get("status") in ["불충분", "없음"]])
        } 