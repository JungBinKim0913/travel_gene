import streamlit as st
import requests
import json
from datetime import datetime, timezone
import base64

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
if "auto_process_message" not in st.session_state:
    st.session_state.auto_process_message = False

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

def generate_share_url(plan_data):
    """여행 계획 데이터를 URL로 인코딩"""   
    if not plan_data:
        return None
    
    json_str = json.dumps(plan_data, ensure_ascii=False)
    encoded_data = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    base_url = "http://localhost:8501/share"
    share_url = f"{base_url}?plan={encoded_data}"
    
    return share_url

# 채팅 기록이 없을 때 안내 메시지 표시
if not st.session_state.chat_history:
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin-bottom: 20px;'>
        <h2>🌟 Travel Gene에 오신 것을 환영합니다! 🌟</h2>
        <p style='font-size: 18px; margin-bottom: 10px;'>AI가 당신만의 특별한 여행 계획을 만들어드립니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 이런 것들을 도와드려요
        
        ✈️ **맞춤형 여행 계획 수립**  
        🗺️ **일정별 상세 루트 제안**  
        🏨 **숙소 및 맛집 추천**  
        🚗 **교통편 및 이동 경로 안내**  
        💰 **예산에 맞는 계획 조정**  
        🎁 **특별한 경험과 액티비티 제안**
        """)
    
    with col2:
        st.markdown("""
        ### 💬 이렇게 시작해보세요
        
        **"제주도 2박 3일 여행 계획 세워줘"**  
        **"부산 맛집 투어 일정 짜줘"**  
        **"50만원으로 일본 여행 갈 수 있을까?"**  
        **"커플 여행으로 좋은 곳 추천해줘"**  
        **"가족 여행 계획 도와줘"**  
        **"혼자 떠나는 힐링 여행 어때?"**
        """)
    
    st.info("""
    **🚀 빠른 시작**

    **1단계:** 우측 상단의 "Gene에게 주문하기 🎯" 버튼으로 상세한 여행 정보를 입력하거나

    **2단계:** 아래 채팅창에서 자유롭게 여행에 대해 대화하세요!

    **💡 팁:** 구체적으로 말씀하실수록 더 정확한 계획을 세워드릴 수 있어요!
    """)
    
    st.markdown("### 🎨 예시 질문으로 시작해보기")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌊 제주도 여행 계획", type="secondary", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "user", 
                "content": "제주도 2박 3일 여행 계획을 세워주세요. 자연 경관과 맛집을 중심으로 계획해주시면 좋겠어요.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            st.session_state.auto_process_message = True
            st.rerun()
    
    with col2:
        if st.button("🍜 부산 맛집 투어", type="secondary", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "user", 
                "content": "부산 1박 2일 맛집 투어 일정을 짜주세요. 해산물과 부산 대표 음식들을 먹어보고 싶어요.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            st.session_state.auto_process_message = True
            st.rerun()
            
    with col3:
        if st.button("✈️ 해외여행 추천", type="secondary", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "user", 
                "content": "처음 해외여행을 가려고 하는데, 초보자도 쉽게 갈 수 있는 나라와 여행 계획을 추천해주세요.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            st.session_state.auto_process_message = True
            st.rerun()
    
    if st.session_state.show_order_form and not st.session_state.user_preferences:
        st.markdown("---")
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
            budget = st.number_input("예산 (만원)", min_value=0, value=100, step=100, key="budget_input")
        
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

# 채팅 기록이 있을 때는 기존대로 표시
else:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

if st.session_state.current_plan:
    st.markdown("---")
    st.success("🎉 **여행 계획이 완성되었습니다!** 아래에서 확인하고 공유해보세요.")
    
    st.markdown("### 🎉 여행 계획이 완성되었습니다!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔗 공유 링크 생성", key="generate_share_link"):
            st.session_state.show_share_link = True
    
    with col2:
        if st.button("🌐 계획 공유하기", key="share_plan_button", type="primary"):
            st.switch_page("pages/2_share.py")
    
    # 공유 링크가 생성되었을 때 전체 폭으로 표시
    if st.session_state.get('show_share_link', False):
        share_url = generate_share_url(st.session_state.current_plan)
        if share_url:
            st.code(share_url)
            st.success("🎉 공유 링크가 생성되었습니다! 위 링크를 복사해서 친구들에게 전송하세요.")
    
    st.info("💡 '계획 공유하기' 버튼을 누르면 예쁜 공유 페이지로 이동합니다!")
    
    with st.expander("🔍 계획 데이터 확인 (상세보기)", expanded=False):
        st.json(st.session_state.current_plan)
    
    st.markdown("---")

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

def process_ai_response():
    """AI 응답 처리 함수"""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        thinking_msg = st.empty()
        full_response = ""
        has_error = False
        plan_completed = False 
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            with thinking_msg.status("🤔 생각 중...") as status:
                status.write("여행 계획을 세우고 있습니다...")
                
                try:
                    current_context = {
                        "messages": [
                            {
                                "role": msg["role"],
                                "content": msg["content"],
                                "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat())
                            } for msg in st.session_state.chat_history
                        ],
                        "user_preferences": st.session_state.user_preferences,
                        "current_plan": st.session_state.current_plan
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
                                            status.update(label="🎉 여행 계획이 완성되었습니다!", state="complete")
                                            plan_completed = True 
                                            
                                            status.write("공유 버튼이 곧 나타납니다!")
                                            
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
                            
                            if plan_completed:
                                st.rerun()
                
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
            if not plan_completed and (has_error or full_response):
                thinking_msg.empty()

# 자동 처리 플래그 확인
if st.session_state.auto_process_message:
    st.session_state.auto_process_message = False
    process_ai_response()

if prompt := st.chat_input("메시지를 입력하세요"):
    with st.chat_message("user"):
        st.write(prompt)
    
    current_message = {
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    st.session_state.chat_history.append(current_message)
    
    process_ai_response() 