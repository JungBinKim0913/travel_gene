import streamlit as st
import requests
import json
from datetime import datetime, timezone

st.set_page_config(
    page_title="Travel Gene Chat",
    page_icon="✈️",
    layout="wide"
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "threads" not in st.session_state:
    st.session_state.threads = []
if "current_plan" not in st.session_state:
    st.session_state.current_plan = None
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = None
if "show_order_form" not in st.session_state:
    st.session_state.show_order_form = False

with st.sidebar:
    st.title("💬 채팅 기록")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("새 채팅 시작"):
            st.session_state.current_thread_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            st.session_state.chat_history = []
            st.session_state.current_plan = None
            st.session_state.user_preferences = None
            st.session_state.show_order_form = False
            if st.session_state.current_thread_id not in st.session_state.threads:
                st.session_state.threads.append(st.session_state.current_thread_id)
            st.rerun()
    
    with col2:
        if st.button("Gene에게 주문하기 🎯"):
            if not st.session_state.current_thread_id:
                st.session_state.current_thread_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                if st.session_state.current_thread_id not in st.session_state.threads:
                    st.session_state.threads.append(st.session_state.current_thread_id)
            st.session_state.user_preferences = None
            st.session_state.show_order_form = True
            st.rerun()
    
    st.subheader("이전 채팅")
    for thread_id in st.session_state.threads:
        if st.button(f"채팅 #{thread_id}", key=f"thread_{thread_id}"):
            st.session_state.current_thread_id = thread_id
            st.session_state.show_order_form = False
            st.rerun()

st.title("Travel Gene Chat 🗺️")

if st.session_state.show_order_form and not st.session_state.user_preferences:
    st.subheader("✈️ 여행 주문서")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "출발일",
            value=datetime.now().date(),
            format="YYYY-MM-DD",
            key="start_date_input",
            on_change=lambda: setattr(st.session_state, 'end_date_input', st.session_state.start_date_input) if st.session_state.end_date_input < st.session_state.start_date_input else None
        )
        end_date = st.date_input(
            "도착일",
            value=datetime.now().date(),
            format="YYYY-MM-DD",
            key="end_date_input"
        )
        destination = st.text_input("희망 여행지", key="destination_input")
        budget = st.number_input("예산 (만원)", min_value=0, step=100, key="budget_input")
    
    with col2:
        activities = st.multiselect(
            "선호하는 활동",
            ["관광", "쇼핑", "맛집", "문화체험", "자연/아웃도어", "휴식"],
            default=["관광", "맛집"],
            key="activities_input"
        )
        accommodation = st.selectbox(
            "선호하는 숙소 유형",
            ["호텔", "에어비앤비", "호스텔", "리조트"],
            key="accommodation_input"
        )
        transport = st.selectbox(
            "선호하는 이동수단",
            ["대중교통", "렌터카", "택시", "도보/자전거"],
            key="transport_input"
        )
    
    special_requests = st.text_area("특별 요청사항 (선택사항)", key="special_requests_input")
    
    if st.button("여행 계획 시작하기", type="primary", key="submit_button"):
        st.session_state.user_preferences = {
            "travel_dates": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "destination": destination,
            "budget": budget,
            "preferences": {
                "activities": activities,
                "accommodation": accommodation,
                "transport": transport,
                "special_requests": special_requests
            }
        }
        
        # 시작 메시지 추가
        start_message = """안녕하세요! 여행 계획을 도와드리겠습니다. 😊  

입력하신 정보를 확인해보겠습니다:  

🗓️  여행 기간: """ + f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}" + """  
📍  희망 여행지: """ + f"{destination if destination else '미정'}" + """  
💰  예산: """ + f"{budget}만원" + """  
✨  선호하는 활동: """ + f"{', '.join(activities)}" + """  
🏠  숙소 유형: """ + f"{accommodation}" + """  
🚗  이동수단: """ + f"{transport}" + """  """

        if special_requests:
            start_message += "\n✏️  특별 요청사항: " + f"{special_requests}" + "  "
        
        start_message += """

이 주문서를 바탕으로 여행을 계획해드릴까요? 추가로 알고 싶으신 점이나 특별히 원하시는 것이 있다면 말씀해 주세요."""

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": start_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        st.session_state.show_order_form = False
        st.rerun()

chat_container = st.container()

if st.session_state.current_plan:
    with st.expander("현재 여행 계획 📋", expanded=True):
        st.json(st.session_state.current_plan)

with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

def handle_error(error_type: str, details: str = None) -> str:
    error_messages = {
        "server": "죄송합니다. 서버에서 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. 🙇🏻",
        "connection": "서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요. 🔌",
        "timeout": "응답 시간이 초과되었습니다. 다시 시도해 주세요. ⏱️",
        "validation": "입력하신 정보가 올바르지 않습니다. 다시 확인해 주세요. ❌",
        "unknown": "예상치 못한 오류가 발생했습니다. 다시 시도해 주세요. 🔄"
    }
    
    error_msg = error_messages.get(error_type, error_messages["unknown"])
    if details:
        error_msg += f"\n상세 정보: {details}"
    return error_msg

if prompt := st.chat_input("메시지를 입력하세요"):
    with st.chat_message("user"):
        st.write(prompt)
    
    current_message = {
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    st.session_state.chat_history.append(current_message)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        thinking_msg = st.empty()
        full_response = ""
        has_error = False
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            with thinking_msg.status("🤔 생각 중...") as status:
                status.write("여행 계획을 세우고 있습니다...")
                
                try:
                    # 현재 대화 컨텍스트에 user_preferences 추가
                    current_context = {
                        "messages": [
                            {
                                "role": msg["role"],
                                "content": msg["content"],
                                "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat())
                            } for msg in st.session_state.chat_history
                        ],
                        "user_preferences": st.session_state.user_preferences
                    }

                    response = requests.post(
                        "http://localhost:8000/travel/plan",
                        json=current_context,
                        headers=headers,
                        stream=True,
                        timeout=300
                    )
                    
                    if response.status_code != 200:
                        error_msg = handle_error("server", f"Status code: {response.status_code}")
                        message_placeholder.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        has_error = True
                    
                    if not has_error:
                        full_response = ""
                        buffer = ""
                        
                        for line in response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    try:
                                        data = json.loads(line[6:])
                                        
                                        if 'status' in data:
                                            if data['status'] == 'start':
                                                status.write("여행 계획을 생성하고 있습니다...")
                                            elif data['status'] == 'complete':
                                                break
                                        
                                        if 'response' in data:
                                            full_response += data['response']
                                            message_placeholder.markdown(full_response)
                                            status.write("응답을 작성하고 있습니다...")
                                        
                                        if 'has_plan' in data and data['has_plan']:
                                            st.session_state.current_plan = data.get('plan', {})
                                            
                                    except json.JSONDecodeError as e:
                                        error_msg = handle_error("validation", "응답 데이터 형식이 올바르지 않습니다.")
                                        message_placeholder.error(error_msg)
                                        has_error = True
                                        break
                        
                        if full_response and not has_error:
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": full_response
                            })
                
                except requests.exceptions.Timeout:
                    error_msg = handle_error("timeout")
                    message_placeholder.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    has_error = True
                except requests.exceptions.RequestException as e:
                    error_msg = handle_error("connection", str(e))
                    message_placeholder.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    has_error = True
            
        except Exception as e:
            error_msg = handle_error("unknown", str(e))
            message_placeholder.error(error_msg)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg
            })
            has_error = True
        
        finally:
            if has_error or full_response:
                thinking_msg.empty() 