"""
여행 계획 공유 페이지
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.styles import SHARE_PAGE_STYLES
from src.share.share_utils import decode_plan_from_url
from src.share.plan_parser import parse_plan_info
from src.share.renderers import (
    render_llm_trip_header, render_llm_content,
    render_trip_header, render_itinerary,
    render_json_trip_header, render_json_content
)
from src.share.share_components import render_share_options

st.markdown(SHARE_PAGE_STYLES, unsafe_allow_html=True)

st.title("🌐 여행 공유")

shared_plan_result = decode_plan_from_url(st.query_params)
shared_plan = None

if shared_plan_result:
    if isinstance(shared_plan_result, tuple):
        plan, error = shared_plan_result
        if error:
            st.error(error)
            st.stop()
        elif plan is not None:
            shared_plan = plan
    elif isinstance(shared_plan_result, dict):
        shared_plan = shared_plan_result

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
    
    st.markdown("---")
    with st.expander("🔍 계획 데이터 확인 (디버깅용)", expanded=False):
        st.json(shared_plan)

elif 'current_plan' in st.session_state and st.session_state.current_plan:
    plan = st.session_state.current_plan
    
    st.info("💡 채팅에서 생성한 여행 계획이 있습니다!")
    
    with st.expander("🔍 계획 데이터 확인 (디버깅용)", expanded=False):
        st.json(plan)
    
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