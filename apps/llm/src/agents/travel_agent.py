from typing import TypedDict, List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.store.memory import InMemoryStore
from langchain.schema import SystemMessage
from datetime import datetime

class TravelPlannerState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
    plan_data: dict
    required_info: dict
    conversation_state: dict

class TravelPlannerAgent:
    """대화형 여행 계획 에이전트"""
    
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
        
        workflow.add_node("understand_request", self._understand_request)
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("refine_plan", self._refine_plan)
        workflow.add_node("ask_destination", self._ask_destination)
        workflow.add_node("collect_details", self._collect_details)
        
        workflow.set_entry_point("understand_request")

        workflow.add_conditional_edges(
            "understand_request",
            self._determine_next_step,
            {
                "ask_destination": "ask_destination",
                "collect_details": "collect_details",
                "generate": "generate_plan",
                "refine": "refine_plan",
                "end": END
            }
        )
        
        workflow.add_edge("ask_destination", END)
        workflow.add_edge("collect_details", END)
        workflow.add_edge("generate_plan", END)
        workflow.add_edge("refine_plan", END)
        
        return workflow

    def _understand_request(self, state: Dict) -> Dict:
        """사용자 요청 이해"""
        try:
            messages = state.get("messages", [])
            conversation_state = state.get("conversation_state", {})
            
            if not conversation_state:
                conversation_state = {
                    "destination": None,
                    "travel_dates": None,
                    "preferences": [],
                    "details_collected": False,
                    "last_topic": None,
                    "pending_questions": [],
                    "confirmed_info": set(),
                    "context_keywords": set(),
                    "interaction_history": []
                }
            
            if not any(isinstance(msg, SystemMessage) for msg in messages):
                messages.insert(0, SystemMessage(content="""여행 계획을 도와드리는 AI 어시스턴트입니다.
                자연스러운 대화를 통해 맞춤형 여행 계획을 만들어드리겠습니다.
                
                제가 도와드릴 수 있는 것들:
                1. 여행지 추천
                2. 일정 계획
                3. 예산 관리
                4. 맛집/관광지 추천
                5. 교통편 안내"""))
            
            last_messages = messages[-3:] if len(messages) >= 3 else messages
            analysis_prompt = SystemMessage(content="""당신은 여행 대화 분석 전문가입니다. 주어진 대화 내용을 분석하여 정확히 아래 JSON 형식으로만 응답해야 합니다.

            당신의 임무:
            1. 대화에서 명시적으로 언급된 정보만 추출
            2. 추측이나 가정은 절대 하지 않음
            3. 아래 형식을 정확히 준수
            4. 한글이 아닌 정확한 JSON 키 사용

            응답 형식 (이 형식을 정확히 따라야 함):
            {
                "core_info": {
                    "destination": "목적지명 또는 null",
                    "dates": "여행날짜 또는 null",
                    "preferences": ["선호도1", "선호도2"]
                },
                "context": {
                    "current_topic": "현재 주제",
                    "related_to_previous": true,
                    "user_interests": ["관심사1", "관심사2"]
                },
                "next_steps": {
                    "required_info": ["필요정보1", "필요정보2"],
                    "suggested_questions": ["질문1", "질문2"],
                    "recommendations": ["제안1", "제안2"]
                }
            }

            주의사항:
            - 반드시 위 JSON 형식만 사용
            - 다른 설명이나 부가 텍스트 절대 추가하지 않음
            - 모든 키는 영문으로 정확히 사용 (core_info, context, next_steps 등)
            - true/false는 소문자로 사용
            - 알 수 없는 정보는 null 또는 빈 배열([]) 사용
            - 배열은 항상 유효한 값만 포함

            잘못된 응답 예시:
            {
                "핵심정보": {  // (X) 한글 키 사용
                "목적지": "서울",  // (X) 한글 키 사용
                }
            }

            올바른 응답 예시:
            {
                "core_info": {
                    "destination": "서울",
                    "dates": null,
                    "preferences": ["관광", "맛집"]
                },
                "context": {
                    "current_topic": "여행지 선택",
                    "related_to_previous": true,
                    "user_interests": ["도시 관광", "현지 음식"]
                },
                "next_steps": {
                    "required_info": ["여행 날짜"],
                    "suggested_questions": ["언제 여행을 계획하시나요?"],
                    "recommendations": ["서울 시내 관광", "현지 맛집 탐방"]
                }
            }""")
            
            analysis_messages = [analysis_prompt, *last_messages]
            analysis_response = self.llm.invoke(analysis_messages)
            
            try:
                import json
                analysis_result = json.loads(analysis_response.content)
                
                if destination := analysis_result["core_info"].get("destination"):
                    conversation_state["destination"] = destination
                if dates := analysis_result["core_info"].get("dates"):
                    conversation_state["travel_dates"] = dates
                if preferences := analysis_result["core_info"].get("preferences"):
                    current_preferences = set(conversation_state.get("preferences", []))
                    current_preferences.update(preferences)
                    conversation_state["preferences"] = list(current_preferences)
                
                conversation_state["last_topic"] = analysis_result["context"]["current_topic"]
                conversation_state["context_keywords"].update(
                    analysis_result["context"]["user_interests"]
                )
                
                required_info = set(analysis_result["next_steps"]["required_info"])
                conversation_state["pending_questions"] = list(
                    required_info - conversation_state["confirmed_info"]
                )
                
                conversation_state["interaction_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "topic": analysis_result["context"]["current_topic"],
                    "collected_info": list(required_info & conversation_state["confirmed_info"])
                })
                
            except json.JSONDecodeError:
                print("Warning: Failed to parse analysis result")
            
            context_msg = self._create_context_message(conversation_state)
            if context_msg:
                messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
                messages.insert(0, context_msg)
            
            if conversation_state["pending_questions"]:
                next_question = self._select_next_question(
                    conversation_state["pending_questions"],
                    conversation_state["last_topic"],
                    conversation_state["interaction_history"]
                )
                if next_question:
                    response_prompt = SystemMessage(content=f"""현재까지 파악된 정보를 바탕으로 자연스럽게 대화를 이어가주세요.
                    
                    다음 정보가 필요합니다: {next_question}
                    
                    대화 스타일:
                    1. 친근하고 자연스러운 어조 유지
                    2. 이전 대화 내용을 참고하여 맥락 유지
                    3. 열린 질문으로 시작하여 사용자의 선호도를 자세히 파악
                    4. 적절한 예시나 추천사항 포함
                    5. 한 번에 너무 많은 것을 물어보지 않기""")
                    
                    messages.append(response_prompt)
            
            response = self.llm.invoke(messages)
            messages.append(response)
            
            return {
                **state,
                "messages": messages,
                "current_step": "understand_request",
                "conversation_state": conversation_state
            }
        except Exception as e:
            print(f"Error in _understand_request: {str(e)}")
            return {
                **state,
                "messages": messages if 'messages' in locals() else [],
                "current_step": "understand_request",
                "conversation_state": conversation_state if 'conversation_state' in locals() else {}
            }
        
    def _determine_next_step(self, state: Dict) -> str:
        """다음 대화 단계 결정"""
        try:
            messages = state.get("messages", [])
            conversation_state = state.get("conversation_state", {})
            
            has_destination = bool(conversation_state.get("destination"))
            has_dates = bool(conversation_state.get("travel_dates"))
            has_preferences = bool(conversation_state.get("preferences"))
            
            recent_messages = messages[-3:] if len(messages) >= 3 else messages
            plan_keywords = ["계획", "일정", "스케줄", "플랜"]
            
            for msg in recent_messages:
                if isinstance(msg, HumanMessage):
                    content = msg.content.lower()
                    if any(keyword in content for keyword in plan_keywords):
                        if has_destination or has_dates or has_preferences:
                            return "generate"
            
            if not has_destination:
                return "ask_destination"
            
            if not has_dates:
                return "collect_details"
            
            if not has_preferences:
                return "collect_details"
            
            return "generate"
            
        except Exception as e:
            print(f"Error in _determine_next_step: {str(e)}")
            return "end"

    def _select_next_question(self, pending_questions: List[str], last_topic: str, interaction_history: List[Dict]) -> Optional[str]:
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

    def _create_context_message(self, conversation_state: Dict) -> Optional[SystemMessage]:
        """현재 대화 컨텍스트를 바탕으로 시스템 메시지 생성"""
        if not conversation_state:
            return None
            
        context_parts = []
        if destination := conversation_state.get("destination"):
            context_parts.append(f"목적지: {destination}")
        if preferences := conversation_state.get("preferences"):
            context_parts.append(f"선호도: {', '.join(preferences)}")
        if travel_dates := conversation_state.get("travel_dates"):
            context_parts.append(f"여행 기간: {travel_dates}")
            
        if context_parts:
            context_msg = """여행 계획을 도와드리는 AI 어시스턴트입니다.
            현재까지 파악된 정보:
            {}
            
            이 정보를 바탕으로 대화를 이어가겠습니다.""".format("\n".join(context_parts))
            
            return SystemMessage(content=context_msg)
        
        return None

    def _analyze_preferences(self, messages: List[BaseMessage]) -> List[str]:
        """LLM을 사용하여 메시지에서 선호도 분석"""
        if not messages:
            return []
        
        recent_messages = messages[-3:]
        
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
        response = self.llm.invoke(analysis_messages)
        
        try:
            import json
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

    def _ask_destination(self, state: Dict) -> Dict:
        """여행지 문의"""
        messages = state.get("messages", [])
        conversation_state = state.get("conversation_state", {})
        
        previous_preferences = self._analyze_preferences(messages)
        
        if previous_preferences:
            preferences_str = ", ".join(previous_preferences)
            destination_prompt = SystemMessage(content=f"""지금까지 파악된 선호도는 다음과 같습니다:
            {preferences_str}
            
            이러한 선호도를 고려하여 구체적인 여행지나 관련 장소를 추천해주세요.
            이미 특정 지역이 언급되었다면, 그 지역 내에서 적합한 장소들을 추천해주세요.
            
            추천 시 고려사항:
            1. 선호도와 일치하는 장소 우선
            2. 계절/날씨 고려
            3. 이동 편의성
            4. 주변 관광지와의 연계성
            5. 현지 특색""")
        else:
            destination_prompt = SystemMessage(content="""어떤 여행을 원하시는지 자연스럽게 물어보세요.
            예시:
            1. 특정 여행지를 언급했다면 확인
            2. 선호하는 여행 스타일이나 원하는 경험 파악
            3. 여행지 추천이 필요하다면 몇 가지 옵션 제시
            
            대화 가이드:
            1. 열린 질문으로 시작
            2. 구체적인 예시 포함
            3. 단계적으로 선호도 파악
            4. 맥락 유지""")
        
        messages.append(destination_prompt)
        response = self.llm.invoke(messages)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_step": "ask_destination",
            "conversation_state": {
                **conversation_state,
                "preferences": previous_preferences
            }
        }

    def _collect_details(self, state: Dict) -> Dict:
        """세부 정보 수집"""
        messages = state.get("messages", [])
        conversation_state = state.get("conversation_state", {})
        
        missing_info = []
        if not conversation_state.get("travel_dates"):
            missing_info.append("여행 기간")
        if not conversation_state.get("preferences"):
            missing_info.append("선호하는 활동")
            
        if missing_info:
            details_prompt = SystemMessage(content=f"""자연스러운 대화로 다음 정보를 물어보세요:
            - {', '.join(missing_info)}
            한 번에 너무 많은 것을 물어보지 말고, 대화를 이어나가듯이 질문해주세요.""")
            
            messages.append(details_prompt)
            response = self.llm.invoke(messages)
            messages.append(response)
        else:
            conversation_state["details_collected"] = True
        
        return {
            **state,
            "messages": messages,
            "current_step": "collect_details",
            "conversation_state": conversation_state
        }

    def _generate_plan(self, state: Dict) -> Dict:
        """여행 계획 생성"""
        messages = state.get("messages", [])
        conversation_state = state.get("conversation_state", {})

        collected_info = f"""현재까지 파악된 여행 정보:
        - 여행지: {conversation_state.get('destination', '미정')}
        - 여행 기간: {conversation_state.get('travel_dates', '미정')}
        - 선호 사항: {conversation_state.get('preferences', '미정')}
        """

        messages.append(SystemMessage(content=f"""{collected_info}

        위 정보를 바탕으로 여행 계획을 생성해주세요. 부족한 정보는 일반적인 선호도를 반영하여 채워주세요.
        응답은 다음 형식으로 작성해주세요:

        1. 여행 개요
           - 기간
           - 목적지
           - 주요 일정 개요

        2. 일자별 세부 일정
           [각 일자별로]
           - 날짜와 요일
           - 시간대별 활동 계획
           - 이동 수단 및 소요 시간
           - 식사 계획

        3. 준비사항
           - 필수 준비물
           - 사전 예약 필요 사항
           - 현지 정보
           - 주의사항
           - 추천 사항

        4. 대체 옵션
           - 우천시 대체 일정
           - 선택적 추가 활동"""))

        response = self.llm.invoke(messages)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_step": "generate_plan",
            "plan_data": {
                "generated_at": "generate_plan",
                "content": response.content,
                "collected_info": collected_info
            }
        }

    def _refine_plan(self, state: Dict) -> Dict:
        """여행 계획 수정"""
        messages = state.get("messages", [])
        plan_data = state.get("plan_data", {})

        messages.append(SystemMessage(content="""사용자의 피드백을 반영하여 기존 계획을 수정해주세요.
        변경된 부분을 명확히 표시해주세요."""))

        response = self.llm.invoke(messages)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_step": "refine_plan",
            "plan_data": {
                "generated_at": "refine_plan",
                "content": response.content,
                "previous_plan": plan_data.get("content", "")
            }
        }

    def chat(self, messages: List[dict], user_preferences: Optional[Dict] = None) -> dict:
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
            
            initial_state = {
                "messages": base_messages,
                "current_step": "understand_request",
                "plan_data": {},
                "required_info": {},
                "conversation_state": {}
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