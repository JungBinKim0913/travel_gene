"""
여행 계획 데이터 파싱 관련 함수들
"""


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