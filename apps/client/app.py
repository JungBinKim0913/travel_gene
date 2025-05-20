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

with st.sidebar:
    st.title("💬 채팅 기록")
    
    if st.button("새 채팅 시작"):
        st.session_state.current_thread_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        st.session_state.chat_history = []
        st.session_state.current_plan = None
        if st.session_state.current_thread_id not in st.session_state.threads:
            st.session_state.threads.append(st.session_state.current_thread_id)
        st.rerun()
    
    st.subheader("이전 채팅")
    for thread_id in st.session_state.threads:
        if st.button(f"채팅 #{thread_id}", key=f"thread_{thread_id}"):
            st.session_state.current_thread_id = thread_id
            st.rerun()

st.title("Travel Gene Chat 🗺️")
chat_container = st.container()

if st.session_state.current_plan:
    with st.expander("현재 여행 계획 📋", expanded=True):
        st.json(st.session_state.current_plan)

with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

if prompt := st.chat_input("메시지를 입력하세요"):
    with st.chat_message("user"):
        st.write(prompt)
    
    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            response = requests.post(
                "http://localhost:8000/travel/plan",
                json=[{
                    "role": "user",
                    "content": prompt,
                    "timestamp": current_time
                }],
                headers=headers,
                stream=True
            )
            
            if response.status_code != 200:
                st.error(f"API 오류 ({response.status_code}): {response.json()}")
            else:
                full_response = ""
                buffer = ""
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                
                                if 'response' in data:
                                    full_response += data['response']
                                    message_placeholder.markdown(full_response)
                                
                                if 'has_plan' in data and data['has_plan']:
                                    st.session_state.current_plan = data.get('plan', {})
                                    
                            except json.JSONDecodeError:
                                continue
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response
                })
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}") 