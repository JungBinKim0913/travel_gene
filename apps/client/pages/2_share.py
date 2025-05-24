import streamlit as st
import json
from datetime import datetime
from urllib.parse import urlencode
import base64
import streamlit.components.v1 as components

st.markdown("""
<style>
    .trip-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    .day-card {
        background: var(--background-color);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        margin-bottom: 15px;
        border-left: 4px solid #667eea;
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    .activity-item {
        background: var(--secondary-background-color);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #28a745;
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    .share-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
    }
    .trip-stats {
        display: flex;
        justify-content: space-around;
        background: rgba(255,255,255,0.1);
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
    }
    .stat-item {
        text-align: center;
    }
    
    /* 다크모드/라이트모드 대응 */
    :root {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
        --border-color: #e0e0e0;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #2d2d2d;
            --secondary-background-color: #3d3d3d;
            --text-color: #ffffff;
            --border-color: #4d4d4d;
        }
    }
    
    /* Streamlit 다크테마 감지 */
    .stApp[data-theme="dark"] {
        --background-color: #2d2d2d;
        --secondary-background-color: #3d3d3d;
        --text-color: #ffffff;
        --border-color: #4d4d4d;
    }
    
    .stApp[data-theme="light"] {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
        --border-color: #e0e0e0;
    }
    
    /* 강제 다크모드 스타일 (Streamlit 다크테마용) */
    .stApp {
        color-scheme: light dark;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
    }
</style>

<script>
// Streamlit 테마 감지 및 CSS 변수 업데이트
function updateTheme() {
    const stApp = document.querySelector('.stApp');
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches ||
                   document.body.classList.contains('dark') ||
                   stApp?.getAttribute('data-theme') === 'dark';
    
    const root = document.documentElement;
    
    if (isDark) {
        root.style.setProperty('--background-color', '#2d2d2d');
        root.style.setProperty('--secondary-background-color', '#3d3d3d');
        root.style.setProperty('--text-color', '#ffffff');
        root.style.setProperty('--border-color', '#4d4d4d');
    } else {
        root.style.setProperty('--background-color', '#ffffff');
        root.style.setProperty('--secondary-background-color', '#f8f9fa');
        root.style.setProperty('--text-color', '#000000');
        root.style.setProperty('--border-color', '#e0e0e0');
    }
}

// 페이지 로드시 및 테마 변경시 실행
document.addEventListener('DOMContentLoaded', updateTheme);
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme);

// MutationObserver로 Streamlit 테마 변경 감지
const observer = new MutationObserver(updateTheme);
observer.observe(document.body, { 
    attributes: true, 
    attributeFilter: ['class', 'data-theme'],
    subtree: true 
});

// 초기 실행
setTimeout(updateTheme, 100);
</script>
""", unsafe_allow_html=True)

def generate_share_url(plan_data):
    """여행 계획 데이터를 URL로 인코딩"""
    if not plan_data:
        return None
    
    json_str = json.dumps(plan_data, ensure_ascii=False)
    encoded_data = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    base_url = "http://localhost:8501/여행공유"
    share_url = f"{base_url}?plan={encoded_data}"
    
    return share_url

def decode_plan_from_url():
    """URL 파라미터에서 여행 계획 데이터 디코딩"""
    try:
        if 'plan' in st.query_params:
            encoded_data = st.query_params['plan']
            json_str = base64.urlsafe_b64decode(encoded_data.encode('utf-8')).decode('utf-8')
            return json.loads(json_str)
    except Exception as e:
        st.error(f"공유 링크를 불러오는 중 오류가 발생했습니다: {e}")
    return None

def render_trip_header(plan):
    """여행 헤더 렌더링"""
    destination = plan.get('destination', '여행지 미정')
    start_date = plan.get('travel_dates', {}).get('start', '')
    end_date = plan.get('travel_dates', {}).get('end', '')
    budget = plan.get('budget', 0)
    
    st.markdown(f"""
    <div class="trip-card">
        <h1>🗺️ {destination} 여행</h1>
        <div class="trip-stats">
            <div class="stat-item">
                <h3>📅</h3>
                <p>{start_date} ~ {end_date}</p>
            </div>
            <div class="stat-item">
                <h3>💰</h3>
                <p>{budget}만원</p>
            </div>
            <div class="stat-item">
                <h3>📍</h3>
                <p>{len(plan.get('itinerary', []))}일 일정</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_itinerary(itinerary):
    """일정 렌더링"""
    for day_num, day_plan in enumerate(itinerary, 1):
        st.markdown(f"""
        <div class="day-card">
            <h3>🌅 {day_num}일차 - {day_plan.get('date', '')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        activities = day_plan.get('activities', [])
        for activity in activities:
            time = activity.get('time', '')
            title = activity.get('title', '')
            description = activity.get('description', '')
            location = activity.get('location', '')
            
            st.markdown(f"""
            <div class="activity-item">
                <strong>⏰ {time} - {title}</strong><br>
                📍 {location}<br>
                <small>{description}</small>
            </div>
            """, unsafe_allow_html=True)

def render_share_options(plan):
    """공유 옵션 렌더링"""
    st.markdown("### 🔗 공유하기")
    
    col1, col2, col3 = st.columns(3)
    
    copy_clicked = False
    kakao_clicked = False
    email_clicked = False
    
    with col1:
        copy_clicked = st.button("📋 링크 복사", key="copy_link")
    
    with col2:
        kakao_clicked = st.button("📱 카카오톡 공유", key="kakao_share")
    
    with col3:
        email_clicked = st.button("📧 이메일 전송", key="email_share")
    
    if copy_clicked:
        share_url = generate_share_url(plan)
        if share_url:
            clipboard_js = f"""
            <div style="height: 50px; opacity: 0;">
                <script>
                // DOM이 완전히 로드된 후 실행
                document.addEventListener('DOMContentLoaded', function() {{
                    setTimeout(function() {{
                        copyToClipboardAndShowDialog();
                    }}, 50);
                }});
                
                // 페이지가 이미 로드된 경우를 위한 즉시 실행
                if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                    setTimeout(function() {{
                        copyToClipboardAndShowDialog();
                    }}, 50);
                }}
                
                function copyToClipboardAndShowDialog() {{
                    const url = "{share_url}";
                    
                    // 첫 번째 시도: navigator.clipboard (HTTPS 환경에서만)
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(url).then(function() {{
                            showSuccessDialog();
                        }}).catch(function(err) {{
                            console.log('Clipboard API 실패, execCommand 시도:', err);
                            fallbackCopyTextToClipboard(url);
                        }});
                    }} else {{
                        // 두 번째 시도: execCommand
                        fallbackCopyTextToClipboard(url);
                    }}
                }}
                
                function fallbackCopyTextToClipboard(text) {{
                    try {{
                        const textArea = document.createElement("textarea");
                        textArea.value = text;
                        textArea.style.position = "fixed";
                        textArea.style.top = "0";
                        textArea.style.left = "0";
                        textArea.style.width = "2em";
                        textArea.style.height = "2em";
                        textArea.style.padding = "0";
                        textArea.style.border = "none";
                        textArea.style.outline = "none";
                        textArea.style.boxShadow = "none";
                        textArea.style.background = "transparent";
                        textArea.style.fontSize = "16px"; // iOS Safari 줌 방지
                        
                        document.body.appendChild(textArea);
                        
                        // iOS Safari 지원
                        if (navigator.userAgent.match(/ipad|iphone/i)) {{
                            const range = document.createRange();
                            range.selectNodeContents(textArea);
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            textArea.setSelectionRange(0, 999999);
                        }} else {{
                            textArea.select();
                            textArea.setSelectionRange(0, 999999);
                        }}
                        
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (successful) {{
                            showSuccessDialog();
                        }} 
                    }} catch (err) {{
                        console.log('execCommand 실패:', err);
                    }}
                }}
                
                function showSuccessDialog() {{
                    showDialog('✅ 링크가 복사되었습니다!', 'rgba(40, 167, 69, 0.9)');
                }}
                
                function showErrorDialog() {{
                    showDialog('❌ 복사에 실패했습니다', 'rgba(220, 53, 69, 0.9)');
                }}
                
                function showDialog(message, bgColor, duration = 3000) {{
                    // 기존 다이얼로그 제거
                    const existingDialog = document.getElementById('copyDialog');
                    if (existingDialog) {{
                        existingDialog.remove();
                    }}
                    
                    // 다이얼로그 생성
                    const dialog = document.createElement('div');
                    dialog.id = 'copyDialog';
                    dialog.style.cssText = `
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: ${{bgColor}};
                        color: white;
                        padding: 20px 30px;
                        border-radius: 10px;
                        font-family: "Source Sans Pro", sans-serif;
                        font-size: 16px;
                        font-weight: 600;
                        z-index: 9999;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                        backdrop-filter: blur(10px);
                        text-align: center;
                        min-width: 250px;
                        max-width: 90vw;
                    `;
                    dialog.innerHTML = message;
                    
                    document.body.appendChild(dialog);
                    
                    // 지정된 시간 후 제거
                    setTimeout(function() {{
                        if (dialog && dialog.parentNode) {{
                            dialog.parentNode.removeChild(dialog);
                        }}
                    }}, duration);
                }}
                </script>
            </div>
            """
            
            components.html(clipboard_js, height=50)
            
            st.markdown("**📋 공유 링크:**")
            st.code(share_url, language=None)
            
            st.info("💡 **Mac 사용자 안내**: 자동 복사가 실패할 경우, 위의 링크를 직접 선택하여 ⌘+C로 복사해주세요!")
    
    elif kakao_clicked:
        st.info("📱 카카오톡 공유 기능은 개발 예정입니다.")
    
    elif email_clicked:
        st.info("📧 이메일 전송 기능은 개발 예정입니다.")

st.title("🌐 여행 공유")

shared_plan = decode_plan_from_url()

if shared_plan:
    st.success("🎉 공유된 여행 계획을 불러왔습니다!")
    
    render_trip_header(shared_plan)
    
    if 'itinerary' in shared_plan and shared_plan['itinerary']:
        st.markdown("## 📅 여행 일정")
        render_itinerary(shared_plan['itinerary'])
    
    if 'preferences' in shared_plan:
        prefs = shared_plan['preferences']
        
        st.markdown("## ✨ 여행 선호사항")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'activities' in prefs:
                st.markdown(f"**🎯 선호 활동:** {', '.join(prefs['activities'])}")
            if 'accommodation' in prefs:
                st.markdown(f"**🏠 숙소 유형:** {prefs['accommodation']}")
        
        with col2:
            if 'transport' in prefs:
                st.markdown(f"**🚗 이동수단:** {prefs['transport']}")
            if 'special_requests' in prefs and prefs['special_requests']:
                st.markdown(f"**✏️ 특별 요청:** {prefs['special_requests']}")

elif 'current_plan' in st.session_state and st.session_state.current_plan:
    plan = st.session_state.current_plan
    
    st.info("💡 채팅에서 생성한 여행 계획이 있습니다!")
    
    render_trip_header(plan)
    
    if 'itinerary' in plan and plan['itinerary']:
        st.markdown("## 📅 여행 일정")
        render_itinerary(plan['itinerary'])
        
        st.markdown("---")
        render_share_options(plan)
    else:
        st.warning("여행 일정이 아직 생성되지 않았습니다.")

else:
    st.markdown("""
    ### 🚀 여행 계획을 공유해보세요!
    
    여행 계획을 공유하는 방법:
    
    1. **채팅 페이지**에서 AI와 여행 계획 완성
    2. 이 페이지에서 **공유 링크 생성**
    3. 친구들에게 **링크 전송**
    
    또는 공유받은 링크를 직접 입력하세요:
    """)
    
    manual_link = st.text_input("🔗 공유 링크 입력", placeholder="https://...")
    
    if manual_link and 'plan=' in manual_link:
        try:
            plan_param = manual_link.split('plan=')[1].split('&')[0]
            json_str = base64.urlsafe_b64decode(plan_param.encode('utf-8')).decode('utf-8')
            decoded_plan = json.loads(json_str)
            
            st.success("✅ 여행 계획을 성공적으로 불러왔습니다!")
            
            render_trip_header(decoded_plan)
            
            if 'itinerary' in decoded_plan and decoded_plan['itinerary']:
                st.markdown("## 📅 여행 일정")
                render_itinerary(decoded_plan['itinerary'])
                
        except Exception as e:
            st.error("❌ 올바르지 않은 공유 링크입니다.")
    
    st.markdown("---")
    st.markdown("### 🎨 공유 페이지 미리보기")
    
    sample_plan = {
        "destination": "제주도",
        "travel_dates": {
            "start": "2024-03-15",
            "end": "2024-03-17"
        },
        "budget": 500,
        "itinerary": [
            {
                "date": "2024-03-15",
                "activities": [
                    {
                        "time": "09:00",
                        "title": "제주공항 도착",
                        "location": "제주국제공항",
                        "description": "렌터카 픽업"
                    },
                    {
                        "time": "11:00", 
                        "title": "성산일출봉",
                        "location": "서귀포시",
                        "description": "UNESCO 세계자연유산 관람"
                    },
                    {
                        "time": "14:00",
                        "title": "점심 - 흑돼지구이",
                        "location": "성산읍",
                        "description": "제주 대표 음식 체험"
                    }
                ]
            }
        ],
        "preferences": {
            "activities": ["관광", "맛집"],
            "accommodation": "호텔",
            "transport": "렌터카"
        }
    }
    
    render_trip_header(sample_plan)
    
    st.markdown("## 📅 여행 일정")
    render_itinerary(sample_plan['itinerary'])
    
    render_share_options(sample_plan) 