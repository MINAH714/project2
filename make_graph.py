import streamlit as st
import json
import pandas as pd
import plotly.express as px
from collections import Counter
import plotly.graph_objects as go

# JSON 파일 로드
@st.cache_data
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 파일 경로 지정
json_file_path = 'dialogue_report_with_emotions_Peter_20250620.json'
json_data = load_data(json_file_path)

st.title("Peter의 감정 분석 대시보드")

# 1. 채팅별 감정 육각형 그래프 (레이더 차트)
st.header("1. 채팅별 감정 분포 (육각형 차트)")

# 각 채팅의 Peter 감정 데이터 추출 및 카운트
chat_emotions_data = []
for i, chat_session in enumerate(json_data):
    # 'timestamp' 필드가 없는 경우 인덱스로 대체 (JSON 구조를 따름)
    chat_identifier = chat_session.get('timestamp', f"알 수 없음 (채팅 {i+1})")
    chat_id = f"채팅 {i+1} (날짜: {chat_identifier})"
    
    peter_emotions = []
    # 'conversation' 필드 확인
    if 'conversation' in chat_session and isinstance(chat_session['conversation'], list):
        for utterance in chat_session['conversation']:
            # 'speaker'가 'Peter'인 경우에만 감정 추출
            if utterance.get('speaker') == 'Peter' and 'emotions' in utterance and isinstance(utterance['emotions'], list):
                peter_emotions.extend(utterance['emotions'])

    emotion_counts = Counter(peter_emotions)
    
    # 모든 가능한 감정 목록을 정의합니다. (데이터에 없는 감정은 0으로 표시)
    # 현재 JSON 데이터에서 발견된 감정들을 기반으로 목록을 만듭니다.
    # 만약 특정 감정들이 항상 포함되어야 한다면, 이 목록을 수동으로 정의할 수 있습니다.
    all_emotions_set = set()
    for session in json_data:
        if 'conversation' in session and isinstance(session['conversation'], list):
            for utterance in session['conversation']:
                if 'emotions' in utterance and isinstance(utterance['emotions'], list):
                    all_emotions_set.update(utterance['emotions'])
    all_emotions_list = sorted(list(all_emotions_set)) # 일관된 순서를 위해 정렬

    # 레이더 차트를 위한 데이터프레임 생성
    df_emotions = pd.DataFrame([{'emotion': emotion, 'count': emotion_counts.get(emotion, 0)} for emotion in all_emotions_list])
    df_emotions['chat_id'] = chat_id
    chat_emotions_data.append(df_emotions)

if chat_emotions_data:
    # 전체 채팅 목록 (셀렉트 박스용)
    chat_options = [df['chat_id'].iloc[0] for df in chat_emotions_data]
    selected_chat = st.selectbox("분석할 채팅을 선택하세요:", chat_options)

    # 선택된 채팅에 해당하는 데이터 필터링
    selected_df_emotions = next((df for df in chat_emotions_data if df['chat_id'].iloc[0] == selected_chat), None)

    if selected_df_emotions is not None:
        # 데이터가 비어있지 않고, 감정 데이터가 있는지 확인
        if not selected_df_emotions.empty and selected_df_emotions['count'].sum() > 0:
            fig_radar = px.line_polar(selected_df_emotions, r='count', theta='emotion', line_close=True,
                                    title=f"{selected_chat} - Peter의 감정 분포",
                                    template="plotly_white", # 이미지와 유사한 밝은 템플릿 사용
                                    color_discrete_sequence=["indianred"]) # 색상 조정
            fig_radar.update_traces(fill='toself', fillcolor='rgba(205, 92, 92, 0.4)') # 내부 채우기 색상 조정
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, selected_df_emotions['count'].max() * 1.1] # 축 범위 자동 조정
                    )
                ),
                font=dict(family="Noto Sans CJK KR", size=12, color="black"), # 폰트 설정 (한글 지원)
                title_font_size=16
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning(f"선택된 채팅 '{selected_chat}'에는 Peter의 감정 데이터가 없거나 모든 감정의 갯수가 0입니다.")
    else:
        st.error("선택된 채팅을 찾을 수 없습니다.")
else:
    st.info("분석할 채팅 데이터가 없습니다. JSON 파일을 확인해주세요.")


# 2. 주간 주감정 변화 그래프
st.header("2. 주간 Peter의 주 감정 변화")

weekly_main_emotions = []

for chat_session in json_data:
    timestamp = chat_session.get('timestamp')
    if not timestamp: # 타임스탬프가 없는 경우 건너김
        continue

    peter_emotions_day = []
    if 'conversation' in chat_session and isinstance(chat_session['conversation'], list):
        for utterance in chat_session['conversation']:
            if utterance.get('speaker') == 'Peter' and 'emotions' in utterance and isinstance(utterance['emotions'], list):
                peter_emotions_day.extend(utterance['emotions'])
    
    if peter_emotions_day:
        emotion_counts_day = Counter(peter_emotions_day)
        # 가장 많이 발생한 감정 (동률일 경우 첫 번째 감정)
        most_common_emotion = emotion_counts_day.most_common(1)[0][0]
        weekly_main_emotions.append({'날짜': pd.to_datetime(timestamp), '주감정': most_common_emotion})

if weekly_main_emotions:
    df_weekly = pd.DataFrame(weekly_main_emotions)
    df_weekly = df_weekly.sort_values(by='날짜').reset_index(drop=True)

    # Plotly Scatter (or Line) 그래프로 주감정 변화 시각화
    fig_weekly = px.scatter(df_weekly, x='날짜', y='주감정', 
                            title="Peter의 일별 주 감정 변화",
                            labels={'날짜': '날짜', '주감정': '주 감정'},
                            color='주감정', # 감정별 색상 구분
                            size=[50]*len(df_weekly), # 점 크기 고정 (원하는 크기로 조절)
                            hover_data={'날짜': "|%Y-%m-%d", '주감정': True}, # 호버 정보
                            template="plotly_white") # 템플릿 변경
    
    fig_weekly.update_traces(marker=dict(symbol='circle', size=15, opacity=0.8)) # 마커 모양 및 크기, 투명도 조정
    fig_weekly.update_layout(xaxis_title="날짜", yaxis_title="주 감정", yaxis_tickangle=-45,
                             font=dict(family="Noto Sans CJK KR", size=12, color="black"), # 폰트 설정 (한글 지원)
                             title_font_size=16) 
    
    # Y축 순서 고정 (선택 사항: 감정의 중요도나 빈도에 따라 수동으로 순서를 정할 수 있음)
    # 데이터에 등장하는 모든 감정을 Y축 순서에 반영
    all_emotions_for_y_axis = sorted(list(df_weekly['주감정'].unique()))
    fig_weekly.update_yaxes(categoryorder='array', categoryarray=all_emotions_for_y_axis)


    st.plotly_chart(fig_weekly, use_container_width=True)
else:
    st.info("Peter의 주간 감정 변화를 분석할 데이터가 충분하지 않습니다. JSON 파일을 확인해주세요.")