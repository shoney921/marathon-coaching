import streamlit as st
from datetime import datetime, timedelta

def create_activity_calendar(activities):
    # 활동 데이터를 날짜별로 그룹화
    activity_by_date = {}
    for activity in activities:
        date = datetime.fromisoformat(activity['local_start_time'].replace('Z', '+00:00')).date()
        if date not in activity_by_date:
            activity_by_date[date] = []
        activity_by_date[date].append(activity)
    
    # CSS 스타일 정의 수정
    st.markdown("""
        <style>
        .calendar-wrapper {
            width: 100%;
            display: flex;
            flex-direction: column;
        }
        .calendar-container {
            display: flex;
            flex-direction: row;
            gap: 2px;
            padding: 10px;
            background-color: #f6f8fa;
            border-radius: 6px;
            width: 100%;
        }
        .week-column {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1;
        }
        .calendar-day {
            width: 100%;
            aspect-ratio: 1;
            border-radius: 1px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: #666;
            position: relative;
        }
        .weekday-label {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 10px;
            color: #666;
            font-weight: bold;
            z-index: 1;
        }
        .month-label {
            position: absolute;
            top: 2px;
            left: 2px;
            font-size: 8px;
            color: #666;
            opacity: 0.7;
        }
        .activity-level-0 { background-color: #ebedf0; }
        .activity-level-1 { background-color: #9be9a8; }
        .activity-level-2 { background-color: #40c463; }
        .activity-level-3 { background-color: #30a14e; }
        .activity-level-4 { background-color: #216e39; }
        .activity-level-5 { background-color: #FF4500; }
        .activity-level-6 { background-color: #B22222; }
        .activity-level-7 { background-color: #8B0000; }
        .calendar-footer {
            display: flex;
            margin-top: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 현재 날짜 기준으로 최근 365일의 캘린더 생성
    today = datetime.now().date()
    
    # 시작 날짜 계산 (365일 전)
    start_date = today - timedelta(days=364)  # 364일 전부터 시작 (365일 포함)
    
    # 시작 날짜의 요일을 기준으로 시작 날짜 조정 (일요일이 첫 번째 열에 오도록)
    days_to_subtract = start_date.weekday() + 1  # 0(월요일)부터 6(일요일)까지
    start_date = start_date - timedelta(days=days_to_subtract)
    
    calendar_html = '<div class="calendar-wrapper">'
    calendar_html += '<div class="calendar-body">'
    calendar_html += '<div class="calendar-container">'
    
    # 요일 레이블을 포함한 주 단위로 캘린더 생성
    weekdays = ['일', '월', '화', '수', '목', '금', '토']
    
    # 총 주 수 계산 (시작 날짜부터 오늘까지)
    total_weeks = (today - start_date).days // 7 + 1
    
    for week in range(total_weeks):
        week_html = '<div class="week-column">'
        for day in range(7):
            date = start_date + timedelta(days=week * 7 + day)
            
            # 365일 이전의 날짜는 표시하지 않음
            if date < (today - timedelta(days=364)):
                week_html += '<div class="calendar-day" style="background-color: transparent;">'
                if week == 0:
                    week_html += f'<span class="weekday-label">{weekdays[day]}</span>'
                week_html += '</div>'
                continue
            
            # 현재 날짜를 넘어가면 빈 칸으로 표시
            if date > today:
                week_html += '<div class="calendar-day" style="background-color: transparent;">'
                if week == 0:
                    week_html += f'<span class="weekday-label">{weekdays[day]}</span>'
                week_html += '</div>'
                continue
            
            # 첫 번째 컬럼에만 요일 레이블 추가
            weekday_label = weekdays[day] if week == 0 else ""
            
            # 월이 시작하는 날에 월 레이블 추가
            month_label = f"{date.month}" if date.day == 1 else ""
            
            # 해당 날짜의 활동이 있는지 확인
            if date in activity_by_date:
                activities = activity_by_date[date]
                total_distance = sum(float(a['distance']) for a in activities)
                
                # 거리에 따른 활동 레벨 결정
                if total_distance >= 42:  # 풀 마라톤
                    level = 7
                    color = "#8B0000"  # 진한 빨간색
                elif total_distance >= 30:
                    level = 6
                    color = "#B22222"  # 벽돌색
                elif total_distance >= 21:  # 하프 마라톤
                    level = 5
                    color = "#DC143C"  # 진한 빨간색
                elif total_distance >= 15:
                    level = 4
                    color = "#FF4500"  # 주황빛 빨간색
                elif total_distance >= 10:
                    level = 3
                    color = "#FF8C00"  # 진한 주황색
                elif total_distance >= 5:
                    level = 2
                    color = "#FFA500"  # 주황색
                elif total_distance > 0:
                    level = 1
                    color = "#32CD32"  # 라임 그린
                else:
                    level = 0
                    color = "#90EE90"  # 연한 초록색

                # 레벨에 따른 설명 추가
                level_descriptions = {
                    7: "풀 마라톤 (42.195km)",
                    6: "장거리 훈련 (30km+)",
                    5: "하프 마라톤 (21.0975km)",
                    4: "중장거리 훈련 (15km+)",
                    3: "중거리 훈련 (10km+)",
                    2: "단거리 훈련 (5km+)",
                    1: "가벼운 운동",
                    0: "휴식"
                }
                
                tooltip = f"{date.strftime('%Y-%m-%d')}<br>총 거리: {total_distance:.1f}km"
                day_html = f'<div class="calendar-day activity-level-{level}" title="{tooltip}" style="background-color: {color};">'
                if weekday_label:
                    day_html += f'<span class="weekday-label">{weekday_label}</span>'
                if month_label:
                    day_html += f'<span class="month-label">{month_label}</span>'
                day_html += '</div>'
                week_html += day_html
            else:
                day_html = f'<div class="calendar-day activity-level-0">'
                if weekday_label:
                    day_html += f'<span class="weekday-label">{weekday_label}</span>'
                if month_label:
                    day_html += f'<span class="month-label">{month_label}</span>'
                day_html += '</div>'
                week_html += day_html
        
        week_html += '</div>'
        calendar_html += week_html
    
    calendar_html += '</div></div>'
    
    # 활동 레벨 설명 추가
    calendar_html_description = """
        <div class="calendar-legend" style="margin-top: 15px; padding: 10px; background-color: #f6f8fa; border-radius: 6px;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #8B0000; border-radius: 3px;"></div>
                    <span>풀 마라톤 (42km+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #B22222; border-radius: 3px;"></div>
                    <span>장거리 훈련 (30km+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #DC143C; border-radius: 3px;"></div>
                    <span>하프 마라톤 (21km+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #FF4500; border-radius: 3px;"></div>
                    <span>중장거리 훈련 (15km+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #FF8C00; border-radius: 3px;"></div>
                    <span>중거리 훈련 (10km+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #FFA500; border-radius: 3px;"></div>
                    <span>단거리 훈련 (5km+)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 15px; height: 15px; background-color: #32CD32; border-radius: 3px;"></div>
                    <span>가벼운 운동</span>
                </div>
            </div>
        </div>
    """
    st.markdown(calendar_html, unsafe_allow_html=True)
    st.markdown(calendar_html_description, unsafe_allow_html=True)