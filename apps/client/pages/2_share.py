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
    
    :root {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
        --border-color: #e0e0e0;
        --muted-text-color: #666666;
        --light-text-color: #888888;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #2d2d2d;
            --secondary-background-color: #3d3d3d;
            --text-color: #ffffff;
            --border-color: #4d4d4d;
            --muted-text-color: #cccccc;
            --light-text-color: #aaaaaa;
        }
    }
    
    .stApp[data-theme="dark"] {
        --background-color: #2d2d2d;
        --secondary-background-color: #3d3d3d;
        --text-color: #ffffff;
        --border-color: #4d4d4d;
        --muted-text-color: #cccccc;
        --light-text-color: #aaaaaa;
    }
    
    .stApp[data-theme="light"] {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
        --border-color: #e0e0e0;
        --muted-text-color: #666666;
        --light-text-color: #888888;
    }
    
    .stApp {
        color-scheme: light dark;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
    }
</style>

<script>
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
        root.style.setProperty('--muted-text-color', '#cccccc');
        root.style.setProperty('--light-text-color', '#aaaaaa');
    } else {
        root.style.setProperty('--background-color', '#ffffff');
        root.style.setProperty('--secondary-background-color', '#f8f9fa');
        root.style.setProperty('--text-color', '#000000');
        root.style.setProperty('--border-color', '#e0e0e0');
        root.style.setProperty('--muted-text-color', '#666666');
        root.style.setProperty('--light-text-color', '#888888');
    }
}

document.addEventListener('DOMContentLoaded', updateTheme);
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme);

const observer = new MutationObserver(updateTheme);
observer.observe(document.body, { 
    attributes: true, 
    attributeFilter: ['class', 'data-theme'],
    subtree: true 
});

setTimeout(updateTheme, 100);
</script>
""", unsafe_allow_html=True)

def generate_share_url(plan_data):
    """여행 계획 데이터를 URL로 인코딩"""
    if not plan_data:
        return None
    
    json_str = json.dumps(plan_data, ensure_ascii=False)
    encoded_data = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    base_url = "http://localhost:8501/share"
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

def parse_plan_info(plan):
    """LLM 계획 데이터에서 정보 파싱"""
    info = {
        'destination': '여행지 미정',
        'start_date': '미정',
        'end_date': '미정', 
        'budget': 0,
        'activities': [],
        'content': ''
    }
    
    if 'plan_data' in plan and isinstance(plan['plan_data'], dict):
        plan_data = plan['plan_data']
        
        if 'travel_overview' in plan_data:
            overview = plan_data['travel_overview']
            info['destination'] = overview.get('destination', '여행지 미정')
            info['start_date'] = overview.get('start_date', '미정')
            info['end_date'] = overview.get('end_date', '미정')
        
        return info
    
    if 'collected_info' in plan:
        collected = plan['collected_info']
        
        if '여행지:' in collected:
            try:
                destination = collected.split('여행지:')[1].split('\n')[0].strip()
                if destination and destination != '':
                    info['destination'] = destination
            except:
                pass
        
        if '여행 기간:' in collected:
            try:
                period = collected.split('여행 기간:')[1].split('\n')[0].strip()
                if '~' in period:
                    dates = period.split('~')
                    if len(dates) >= 2:
                        info['start_date'] = dates[0].strip()
                        info['end_date'] = dates[1].strip()
                elif period and period != '':
                    info['start_date'] = period
                    info['end_date'] = period
            except:
                pass
        
        if '선호 사항:' in collected:
            try:
                activities_str = collected.split('선호 사항:')[1].split('\n')[0].strip()
                activities_str = activities_str.replace('[', '').replace(']', '').replace("'", '')
                if activities_str:
                    info['activities'] = [act.strip() for act in activities_str.split(',')]
            except:
                pass
    
    if 'content' in plan:
        info['content'] = plan['content']
    
    return info

def parse_itinerary_from_content(content):
    """LLM 내용에서 일정 정보 파싱 - '일자별 세부 일정' 섹션만"""
    itinerary = []
    
    itinerary_section = ""
    lines = content.split('\n')
    
    in_itinerary_section = False
    
    for line in lines:
        line = line.strip()
        
        if '일자별' in line and '일정' in line:
            in_itinerary_section = True
            continue
        
        elif in_itinerary_section and (
            line.startswith('3.') or 
            line.startswith('4.') or 
            '준비사항' in line or 
            '대체 옵션' in line or
            '주의사항' in line
        ):
            break
        
        elif in_itinerary_section:
            itinerary_section += line + '\n'
    
    if not itinerary_section.strip():
        return []
    
    lines = itinerary_section.split('\n')
    current_day = None
    current_activities = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('#'):
            continue
            
        if ('월' in line and '일' in line and ('(' in line or '년' in line)):
            if current_day and current_activities:
                itinerary.append({
                    'date': current_day,
                    'activities': current_activities
                })
            
            current_day = line.replace('-', '').replace('#', '').strip()
            current_activities = []
        
        elif ':' in line and current_day:
            try:
                time = ''
                title = ''
                
                if line.startswith('-') and ': ' in line:
                    line_clean = line.lstrip('-').strip()
                    if ':' in line_clean:
                        parts = line_clean.split(': ', 1)
                        if len(parts) == 2:
                            potential_time = parts[0].strip()
                            potential_title = parts[1].strip()
                            if any(char.isdigit() for char in potential_time) or potential_time in ['오전', '오후', '아침', '점심', '저녁']:
                                time = potential_time
                                title = potential_title
                            else:
                                time = ''
                                title = line_clean
                        else:
                            time = ''
                            title = line_clean
                    else:
                        time = ''
                        title = line_clean
                elif line.startswith('-') and ' - ' in line:
                    line_clean = line.lstrip('-').strip()
                    if ' - ' in line_clean:
                        time_part, activity_part = line_clean.split(' - ', 1)
                        time = time_part.strip()
                        title = activity_part.strip()
                    else:
                        time = ''
                        title = line_clean
                elif ' - ' in line and ':' in line:
                    time_part, activity_part = line.split(' - ', 1)
                    time = time_part.strip()
                    title = activity_part.strip()
                elif ':' in line and not ' - ' in line and not line.startswith('-'):
                    time_part, activity_part = line.split(':', 1)
                    time = time_part.strip()
                    title = activity_part.strip()
                else:
                    time = ''
                    title = line.strip()
                
                activity = {
                    'time': time,
                    'title': title,
                    'location': '',
                    'description': ''
                }
                
                current_activities.append(activity)
                
            except:
                if current_day:
                    activity = {
                        'time': '',
                        'title': line,
                        'location': '',
                        'description': ''
                    }
                    current_activities.append(activity)
        
        elif (line.startswith('○') or line.startswith('o') or line.startswith('•') or 
              line.startswith('-') and not ('월' in line and '일' in line)) and current_day:
            detail = line.replace('○', '').replace('o', '').replace('•', '').replace('-', '').strip()
            if detail:
                if ':' in detail and ' - ' in detail:
                    try:
                        time_part, activity_part = detail.split(' - ', 1)
                        activity = {
                            'time': time_part.strip(),
                            'title': activity_part.strip(),
                            'location': '',
                            'description': ''
                        }
                        current_activities.append(activity)
                    except:
                        pass
                else:
                    activity = {
                        'time': '',
                        'title': detail,
                        'location': '',
                        'description': ''
                    }
                    current_activities.append(activity)
    
    if current_day and current_activities:
        itinerary.append({
            'date': current_day,
            'activities': current_activities
        })
    
    return itinerary

def render_llm_trip_header(plan_info):
    """LLM 계획 정보로 헤더 렌더링"""
    destination = plan_info['destination']
    start_date = plan_info['start_date']
    end_date = plan_info['end_date']
    
    days_count = 0
    if start_date != '미정' and end_date != '미정':
        try:
            from datetime import datetime
            start = datetime.strptime(start_date.split('(')[0].strip(), '%Y년 %m월 %d일')
            end = datetime.strptime(end_date.split('(')[0].strip(), '%Y년 %m월 %d일')
            days_count = (end - start).days + 1
        except:
            days_count = 1
    
    if start_date != '미정' and end_date != '미정':
        date_display = f"{start_date} ~ {end_date}"
    else:
        date_display = "미정"
    
    activities_display = '・'.join(plan_info['activities']) if plan_info['activities'] else '일반 여행'
    
    st.markdown(f"""
    <div class="trip-card">
        <h1>🗺️ {destination} 여행</h1>
        <div style="margin-top: 20px;">
            <div style="margin-bottom: 12px; font-size: 16px;">
                <strong>📅 여행 기간:</strong> {date_display}
            </div>
            <div style="margin-bottom: 12px; font-size: 16px;">
                <strong>📍 여행 일정:</strong> {days_count}일
            </div>
            <div style="margin-bottom: 8px; font-size: 16px;">
                <strong>🎯 여행 활동:</strong> {activities_display}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_llm_content(content):
    """LLM 생성 내용 렌더링"""
    st.markdown("## 📋 여행 계획")
    
    itinerary = parse_itinerary_from_content(content)
    
    if itinerary:
        st.markdown("### 📅 여행 일정")
        render_itinerary(itinerary)
        
        st.markdown("### 📝 추가 정보")
        
        sections = content.split('\n\n')
        for section in sections:
            if section.strip():
                if not any(keyword in section for keyword in ['일자별', '일정', '6월', '7월', '8월', '9월', '10월', '11월', '12월', '1월', '2월', '3월', '4월', '5월']):
                    lines = section.strip().split('\n')
                    if lines:
                        first_line = lines[0].strip()
                        if any(keyword in first_line for keyword in ['준비사항', '대체 옵션', '주의사항']):
                            st.subheader(first_line)
                            if len(lines) > 1:
                                content_lines = '\n'.join(lines[1:])
                                st.markdown(content_lines)
                        elif not any(digit in first_line for digit in '0123456789'):
                            st.markdown(section)
    else:
        sections = content.split('\n\n')
        
        for section in sections:
            if section.strip():
                lines = section.strip().split('\n')
                if lines:
                    first_line = lines[0].strip()
                    if any(keyword in first_line for keyword in ['개요', '일정', '준비사항', '대체 옵션']):
                        st.subheader(first_line)
                        if len(lines) > 1:
                            content_lines = '\n'.join(lines[1:])
                            st.markdown(content_lines)
                    else:
                        st.markdown(section)

def render_trip_header(plan):
    """여행 헤더 렌더링"""
    destination = None
    start_date = None
    end_date = None
    budget = None
    
    if 'destination' in plan:
        destination = plan['destination']
    elif 'user_preferences' in plan and 'destination' in plan['user_preferences']:
        destination = plan['user_preferences']['destination']
    
    if 'travel_dates' in plan:
        start_date = plan['travel_dates'].get('start', '')
        end_date = plan['travel_dates'].get('end', '')
    elif 'user_preferences' in plan and 'travel_dates' in plan['user_preferences']:
        start_date = plan['user_preferences']['travel_dates'].get('start', '')
        end_date = plan['user_preferences']['travel_dates'].get('end', '')
    
    if 'budget' in plan:
        budget = plan['budget']
    elif 'user_preferences' in plan and 'budget' in plan['user_preferences']:
        budget = plan['user_preferences']['budget']
    
    destination = destination or '여행지 미정'
    start_date = start_date or '미정'
    end_date = end_date or '미정'
    budget = budget or 0
    
    itinerary_count = len(plan.get('itinerary', []))
    
    if start_date != '미정' and end_date != '미정':
        date_display = f"{start_date} ~ {end_date}"
    else:
        date_display = "미정"
    
    st.markdown(f"""
    <div class="trip-card">
        <h1>🗺️ {destination} 여행</h1>
        <div style="margin-top: 20px;">
            <div style="margin-bottom: 12px; font-size: 16px;">
                <strong>📅 여행 기간:</strong> {date_display}
            </div>
            <div style="margin-bottom: 12px; font-size: 16px;">
                <strong>💰 여행 예산:</strong> {budget}만원
            </div>
            <div style="margin-bottom: 8px; font-size: 16px;">
                <strong>📍 여행 일정:</strong> {itinerary_count}일
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_itinerary(itinerary):
    """일정 렌더링"""
    for day_num, day_plan in enumerate(itinerary, 1):
        date_display = day_plan.get('date', '').replace('**', '')
        
        st.markdown(f"""
        <div class="day-card">
            <h3>🌅 {day_num}일차 - {date_display}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        activities = day_plan.get('activities', [])
        for activity in activities:
            time = activity.get('time', '').strip()
            title = activity.get('title', '').replace('**', '').strip()
            description = activity.get('description', '').replace('**', '').strip()
            location = activity.get('location', '').replace('**', '').strip()
            
            def get_activity_icon(title_text):
                title_lower = title_text.lower()
                if any(word in title_lower for word in ['이동', '출발', '도착', '픽업', '드롭오프', '교통', '버스', '지하철', '택시', '렌터카']):
                    return '🚗'
                elif any(word in title_lower for word in ['식사', '점심', '저녁', '아침', '브런치', '디너', '맛집', '음식', '식당']):
                    return '🍽️'
                elif any(word in title_lower for word in ['카페', '커피', '빵집']):
                    return '☕️'
                elif any(word in title_lower for word in ['체크인', '체크아웃', '숙소', '호텔', '펜션', '게스트하우스']):
                    return '🏨'
                elif any(word in title_lower for word in ['관광', '투어', '견학', '구경', '방문', '관람']):
                    return '🎯'
                elif any(word in title_lower for word in ['쇼핑', '구매', '마트', '시장', '아울렛']):
                    return '🛍️'
                elif any(word in title_lower for word in ['휴식', '산책', '쉬기', '자유시간']):
                    return '😌'
                else:
                    return '📍'
            
            activity_icon = get_activity_icon(title)
            
            def is_category_title(time):
                category_keywords = ['- 이동 수단', '- 식사 계획', '추천 코스', '대체 옵션', '주의사항']
                return any(keyword in time for keyword in category_keywords)
            
            should_show_time = time and not is_category_title(time)
            
            if should_show_time:
                main_section = f"<div style='margin-bottom: 4px;'><div style='margin-bottom: 2px;'><strong>⏰ {time}</strong></div><div style='margin-left: 8px;'><strong>{activity_icon} {title}</strong></div></div>"
            else:
                main_section = f"<div style='margin-bottom: 20px;'><strong>{activity_icon} {title}</strong></div>"
            
            location_section = ""
            if location:
                location_section = f"<div style='margin-bottom: 4px; color: #666; font-size: 14px;'>📍 {location}</div>"
            
            description_section = ""
            if description:
                description_section = f"<div style='font-size: 13px; color: #888;'>{description}</div>"
            
            activity_html = f"""
            <div class="activity-item">
                {main_section}
                {location_section}
                {description_section}
            </div>
            """
            
            st.markdown(activity_html, unsafe_allow_html=True)

def render_share_options(plan):
    """공유 옵션 렌더링"""
    st.markdown("### 🔗 공유하기")
    
    col1, col2, col3 = st.columns(3)
    
    generate_clicked = False
    kakao_clicked = False
    email_clicked = False
    
    with col1:
        generate_clicked = st.button("📋 링크 생성", key="generate_link")
    
    with col2:
        kakao_clicked = st.button("📱 카카오톡 공유", key="kakao_share")
    
    with col3:
        email_clicked = st.button("📧 이메일 전송", key="email_share")
    
    if generate_clicked:
        share_url = generate_share_url(plan)
        if share_url:
            clipboard_js = f"""
            <div style="height: 50px; opacity: 0;">
                <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    setTimeout(function() {{
                        copyToClipboardAndShowDialog();
                    }}, 50);
                }});
                
                if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                    setTimeout(function() {{
                        copyToClipboardAndShowDialog();
                    }}, 50);
                }}
                
                function copyToClipboardAndShowDialog() {{
                    const url = "{share_url}";
                    
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(url).then(function() {{
                            showSuccessDialog();
                        }}).catch(function(err) {{
                            console.log('Clipboard API 실패, execCommand 시도:', err);
                            fallbackCopyTextToClipboard(url);
                        }});
                    }} else {{
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
                        textArea.style.fontSize = "16px"; 
                        
                        document.body.appendChild(textArea);
                        
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
                    const existingDialog = document.getElementById('copyDialog');
                    if (existingDialog) {{
                        existingDialog.remove();
                    }}
                    
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

def render_json_trip_header(plan_data):
    """JSON 계획 정보로 헤더 렌더링"""
    if 'travel_overview' not in plan_data:
        return
    
    overview = plan_data['travel_overview']
    destination = overview.get('destination', '여행지 미정')
    start_date = overview.get('start_date', '미정')
    end_date = overview.get('end_date', '미정')
    duration_days = overview.get('duration_days', 0)
    summary = overview.get('summary', '')
    
    if start_date != '미정' and end_date != '미정':
        date_display = f"{start_date} ~ {end_date}"
    else:
        date_display = "미정"
    
    st.markdown(f"""
    <div class="trip-card">
        <h1>🗺️ {destination} 여행</h1>
        <div style="margin-top: 20px;">
            <div style="margin-bottom: 12px; font-size: 16px;">
                <strong>📅 여행 기간:</strong> {date_display}
            </div>
            <div style="margin-bottom: 12px; font-size: 16px;">
                <strong>📍 여행 일정:</strong> {duration_days}일
            </div>
            <div style="margin-bottom: 8px; font-size: 16px;">
                <strong>✨ 여행 컨셉:</strong> {summary if summary else '맞춤형 여행'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_json_itinerary(itinerary_data):
    """JSON 형식 일정 렌더링"""
    for day_num, day_plan in enumerate(itinerary_data, 1):
        date = day_plan.get('date', '')
        day_of_week = day_plan.get('day_of_week', '')
        date_display = f"{date} ({day_of_week})" if day_of_week else date
        
        st.markdown(f"""
        <div class="day-card">
            <h3>🌅 {day_num}일차 - {date_display}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        activities = day_plan.get('activities', [])
        for activity in activities:
            time = activity.get('time', '').strip()
            title = activity.get('title', '').strip()
            location = activity.get('location', '').strip()
            address = activity.get('address', '').strip()
            description = activity.get('description', '').strip()
            category = activity.get('category', '').strip()
            
            def get_category_icon(category):
                icon_map = {
                    '식사': '🍽️',
                    '관광': '🎯',
                    '숙박': '🏨',
                    '이동': '🚗',
                    '쇼핑': '🛍️',
                    '휴식': '😌'
                }
                return icon_map.get(category, '📍')
            
            activity_icon = get_category_icon(category)
            
            should_show_time = time and time.strip()
            
            if should_show_time:
                main_section = f"<div style='margin-bottom: 4px; color: var(--text-color);'><div style='margin-bottom: 2px;'><strong>⏰ {time}</strong></div><div><strong>{activity_icon} {title}</strong></div></div>"
            else:
                main_section = f"<div style='margin-bottom: 20px; color: var(--text-color);'><strong>{activity_icon} {title}</strong></div>"
            
            location_section = ""
            if location and address:
                location_section = f"<div style='margin-bottom: 4px; color: var(--text-color); opacity: 0.7; font-size: 14px;'>📍 {location} - {address}</div>"
            elif location:
                location_section = f"<div style='margin-bottom: 4px; color: var(--text-color); opacity: 0.7; font-size: 14px;'>📍 {location}</div>"
            elif address:
                location_section = f"<div style='margin-bottom: 4px; color: var(--text-color); opacity: 0.7; font-size: 14px;'>📍 {address}</div>"
            
            description_section = ""
            if description:
                description_section = f"<div style='font-size: 13px; color: var(--text-color); opacity: 0.6;'>{description}</div>"
            
            activity_html = f"""
            <div class="activity-item">
                {main_section}
                {location_section}
                {description_section}
            </div>
            """
            
            st.markdown(activity_html, unsafe_allow_html=True)

def render_json_additional_info(plan_data):
    """JSON 형식 추가 정보 렌더링"""
    if 'preparation' in plan_data:
        prep = plan_data['preparation']
        st.markdown("### 🎒 준비사항")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'essential_items' in prep and prep['essential_items']:
                st.markdown("**🎁 필수 준비물:**")
                for item in prep['essential_items']:
                    st.markdown(f"• {item}")
            
            if 'reservations_needed' in prep and prep['reservations_needed']:
                st.markdown("**📞 사전 예약 필요:**")
                for reservation in prep['reservations_needed']:
                    st.markdown(f"• {reservation}")
        
        with col2:
            if 'local_tips' in prep and prep['local_tips']:
                st.markdown("**💡 현지 정보:**")
                for tip in prep['local_tips']:
                    st.markdown(f"• {tip}")
            
            if 'warnings' in prep and prep['warnings']:
                st.markdown("**⚠️ 주의사항:**")
                for warning in prep['warnings']:
                    st.markdown(f"• {warning}")
    
    if 'alternatives' in plan_data:
        alt = plan_data['alternatives']
        st.markdown("### 🌦️ 대체 옵션")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'rainy_day_options' in alt and alt['rainy_day_options']:
                st.markdown("**☔ 우천시 대체 장소:**")
                for option in alt['rainy_day_options']:
                    st.markdown(f"• {option}")
        
        with col2:
            if 'optional_activities' in alt and alt['optional_activities']:
                st.markdown("**✨ 선택적 추가 활동:**")
                for activity in alt['optional_activities']:
                    st.markdown(f"• {activity}")

def render_json_content(plan_data):
    """JSON 형식 계획 내용 렌더링"""
    st.markdown("## 📋 여행 계획")
    
    if 'itinerary' in plan_data and plan_data['itinerary']:
        st.markdown("### 📅 여행 일정")
        render_json_itinerary(plan_data['itinerary'])
        
        st.markdown("---")
        render_json_additional_info(plan_data)
    else:
        st.info("📝 여행 일정 정보가 없습니다.")

st.title("🌐 여행 공유")

shared_plan = decode_plan_from_url()

if shared_plan:
    st.success("🎉 공유된 여행 계획을 불러왔습니다!")
    
    if 'plan_data' in shared_plan and isinstance(shared_plan['plan_data'], dict):
        plan_data = shared_plan['plan_data']
        
        render_json_trip_header(plan_data)
        render_json_content(plan_data)
        
    elif 'content' in shared_plan and 'collected_info' in shared_plan:
        plan_info = parse_plan_info(shared_plan)
        
        render_llm_trip_header(plan_info)
        
        if plan_info['content']:
            render_llm_content(plan_info['content'])
        
    else:
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
    
    st.markdown("---")
    render_share_options(shared_plan)

elif 'current_plan' in st.session_state and st.session_state.current_plan:
    plan = st.session_state.current_plan
    
    st.info("💡 채팅에서 생성한 여행 계획이 있습니다!")
    
    if 'plan_data' in plan and isinstance(plan['plan_data'], dict):
        plan_data = plan['plan_data']
        
        render_json_trip_header(plan_data)
        render_json_content(plan_data)
        
    elif 'content' in plan and 'collected_info' in plan:
        plan_info = parse_plan_info(plan)
        
        render_llm_trip_header(plan_info)
        
        if plan_info['content']:
            render_llm_content(plan_info['content'])
        
    else:
        render_trip_header(plan)
        
        if 'itinerary' in plan and plan['itinerary']:
            st.markdown("## 📅 여행 일정")
            render_itinerary(plan['itinerary'])
        else:
            st.markdown("## 📅 여행 일정")
            st.info("📝 여행 일정이 아직 생성되지 않았지만, 기본 계획 정보를 공유할 수 있습니다.")
        
        if 'preferences' in plan:
            prefs = plan['preferences']
            
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
    
    st.markdown("---")
    render_share_options(plan)

else:
    st.markdown("""
    ### 🚀 여행 계획을 공유해보세요!
    
    여행 계획을 공유하는 방법:
    
    1. **채팅 페이지**에서 AI와 여행 계획 완성
    2. 이 페이지에서 **공유 링크 생성**
    3. 친구들에게 **링크 전송**
    """)
    
    
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