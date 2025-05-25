"""
여행 계획 렌더링 관련 함수들
"""
import streamlit as st
from .plan_parser import parse_itinerary_from_content


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