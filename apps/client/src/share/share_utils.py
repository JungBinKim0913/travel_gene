"""
공유 기능 관련 유틸리티 함수들
"""
import json
import base64
from urllib.parse import quote


def generate_share_url(plan_data):
    """여행 계획 데이터를 URL로 인코딩"""
    if not plan_data:
        return None
    
    json_str = json.dumps(plan_data, ensure_ascii=False)
    encoded_data = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    base_url = "http://localhost:8501/share"
    share_url = f"{base_url}?plan={encoded_data}"
    
    return share_url


def decode_plan_from_url(query_params):
    """URL 파라미터에서 여행 계획 데이터 디코딩"""
    try:
        if 'plan' in query_params:
            encoded_data = query_params['plan']
            json_str = base64.urlsafe_b64decode(encoded_data.encode('utf-8')).decode('utf-8')
            return json.loads(json_str)
        else:
            return None
    except Exception as e:
        return None, f"공유 링크를 불러오는 중 오류가 발생했습니다: {e}"


def generate_kakao_share_message(plan):
    """카카오톡 공유용 메시지 생성"""
    if 'plan_data' in plan and isinstance(plan['plan_data'], dict):
        plan_data = plan['plan_data']
        if 'travel_overview' in plan_data:
            overview = plan_data['travel_overview']
            destination = overview.get('destination', '여행지 미정')
            start_date = overview.get('start_date', '미정')
            end_date = overview.get('end_date', '미정')
            duration_days = overview.get('duration_days', 0)
        else:
            destination = '여행지 미정'
            start_date = '미정'
            end_date = '미정'
            duration_days = 0
    elif 'content' in plan and 'collected_info' in plan:
        from .plan_parser import parse_plan_info
        plan_info = parse_plan_info(plan)
        destination = plan_info['destination']
        start_date = plan_info['start_date']
        end_date = plan_info['end_date']
        duration_days = 1
    else:
        destination = plan.get('destination', '여행지 미정')
        start_date = plan.get('travel_dates', {}).get('start', '미정')
        end_date = plan.get('travel_dates', {}).get('end', '미정')
        duration_days = len(plan.get('itinerary', []))
    
    if start_date != '미정' and end_date != '미정':
        date_display = f"{start_date} ~ {end_date}"
    else:
        date_display = "미정"
    
    message = f"""🗺️ {destination} 여행 계획을 공유합니다!

📅 여행 기간: {date_display}
📍 여행 일정: {duration_days}일

✨ 함께 여행 계획을 확인해보세요!"""
    
    return message


def generate_email_content(plan):
    """이메일 전송용 내용 생성"""
    if 'plan_data' in plan and isinstance(plan['plan_data'], dict):
        plan_data = plan['plan_data']
        if 'travel_overview' in plan_data:
            overview = plan_data['travel_overview']
            destination = overview.get('destination', '여행지 미정')
            start_date = overview.get('start_date', '미정')
            end_date = overview.get('end_date', '미정')
            duration_days = overview.get('duration_days', 0)
            summary = overview.get('summary', '')
        else:
            destination = '여행지 미정'
            start_date = '미정'
            end_date = '미정'
            duration_days = 0
            summary = ''
    elif 'content' in plan and 'collected_info' in plan:
        from .plan_parser import parse_plan_info
        plan_info = parse_plan_info(plan)
        destination = plan_info['destination']
        start_date = plan_info['start_date']
        end_date = plan_info['end_date']
        duration_days = 1
        summary = ''
    else:
        destination = plan.get('destination', '여행지 미정')
        start_date = plan.get('travel_dates', {}).get('start', '미정')
        end_date = plan.get('travel_dates', {}).get('end', '미정')
        duration_days = len(plan.get('itinerary', []))
        summary = ''
    
    if start_date != '미정' and end_date != '미정':
        date_display = f"{start_date} ~ {end_date}"
    else:
        date_display = "미정"
    
    subject = f"🗺️ {destination} 여행 계획 공유"
    
    body = f"""안녕하세요!

{destination} 여행 계획을 공유드립니다.

📅 여행 기간: {date_display}
📍 여행 일정: {duration_days}일"""
    
    if summary:
        body += f"\n✨ 여행 컨셉: {summary}"
    
    body += f"""

아래 링크를 클릭하시면 상세한 여행 계획을 확인하실 수 있습니다:
{{share_url}}

즐거운 여행 되세요! 🎉

---
Travel Gene에서 생성된 여행 계획입니다."""
    
    return subject, body 