import streamlit as st

st.set_page_config(
    page_title="Travel Gene",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링 추가
st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 30px;
        width: 100%;
        height: auto;
        min-height: 200px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: left;
        white-space: pre-line;
    }
    .stButton > button:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4c93 100%);
    }
    .stButton > button:focus {
        outline: none;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .stButton > button:active {
        transform: translateY(-2px);
    }
    /* 버튼 내부 텍스트 스타일링 */
    .stButton > button p {
        margin: 0;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🗺️ Travel Gene")
st.subheader("AI와 함께하는 똑똑한 여행 계획")
    
col1, col2 = st.columns(2)

with col1:
    # 카드 스타일 버튼
    chat_text = """💬 여행 채팅

    AI 여행 전문가와 대화하며  
    맞춤형 여행 계획을 세워보세요.
    
• 🎯 개인 맞춤 추천
• 📅 실시간 일정 관리
• 🗺️ 구글 캘린더 연동"""
    
    if st.button(chat_text, key="chat_card", use_container_width=True):
        st.switch_page("pages/1_chat.py")
    
with col2:
    # 카드 스타일 버튼
    share_text = """🌐 여행 공유

    완성된 여행 계획을 친구들과  
    쉽게 공유할 수 있어요.
    
• 📱 모바일 최적화
• 🔗 간편한 링크 공유
• 🎨 예쁜 디자인"""
    
    if st.button(share_text, key="share_card", use_container_width=True):
        st.switch_page("pages/2_share.py")

st.markdown("---")

st.markdown("""
### 🚀 시작하기
위의 카드를 클릭하거나 사이드바에서 원하는 기능을 선택해주세요!

- **채팅**: AI와 대화하며 여행 계획 세우기
- **여행공유**: 완성된 계획 확인하기
""")

with st.sidebar:
    st.markdown("### 📖 사용법")
    st.markdown("""
    1. **채팅 페이지**에서 여행 계획 시작
    2. AI와 대화하며 계획 완성  
    3. **여행공유 페이지**에서 결과 확인
    """) 