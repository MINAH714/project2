import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from collections import Counter
import datetime
import os # os 모듈 추가

# JSON 데이터 로드 함수
@st.cache_data
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 앱 제목
st.title("개인별 감정 분석 대시보드")

# JSON 파일들이 저장된 폴더 (현재 스크립트와 같은 경로의 'data' 폴더를 가정)
data_folder = './' # JSON 파일이 현재 스크립트와 같은 폴더에 있다면 './' 로 설정

# 데이터 폴더에서 JSON 파일 목록 가져오기
try:
    json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
    if not json_files:
        st.error(f"'{data_folder}' 폴더에 JSON 파일이 없습니다. 파일 경로를 확인해주세요.")
        st.stop()
except FileNotFoundError:
    st.error(f"'{data_folder}' 폴더를 찾을 수 없습니다. 파일 경로를 확인해주세요.")
    st.stop()

# 셀렉트 박스로 JSON 파일 선택
selected_file = st.selectbox("분석할 JSON 파일을 선택하세요:", json_files)

if selected_file:
    file_path = os.path.join(data_folder, selected_file)
    data = load_data(file_path)

    # 데이터의 첫 번째 엔트리에서 person_name 추출 (모든 엔트리의 이름이 같다고 가정)
    person_name = data[0]['person_name'] if data and 'person_name' in data[0] else "이름 없음"

    st.header(f"{person_name}님의 감정 분석 결과")

    # --------------------------------------------------------------------------
    # 1. 일별 감정 산포도 (감정별 색상 표시)
    st.subheader(f"1. {person_name}님의 일별 감정 산포도")

    st.markdown("""
    <div style="font-size: small; color: gray;">
        <p>이 그래프는 각 날짜별로 선택된 인물의 발화에 나타난 감정들을 시각화합니다. 각 감정은 고유한 색상으로 표시됩니다.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**{person_name}님의 일별 감정 발화 횟수:**")

    # 각 날짜별 감정 데이터 추출 및 집계
    daily_emotions = {}
    for entry in data:
        date_str = entry['timestamp']
        if date_str not in daily_emotions:
            daily_emotions[date_str] = []
        
        for convo in entry['conversation']:
            if convo['speaker'] == person_name: # 선택된 인물의 감정만 추출
                daily_emotions[date_str].extend(convo['emotions'])

    # 날짜를 기준으로 정렬
    sorted_dates = sorted(daily_emotions.keys())

    # 감정 발화 횟수 출력 (산포도 설명 부분)
    for date_str in sorted_dates:
        emotions_count = Counter(daily_emotions[date_str])
        if emotions_count:
            st.markdown(f"- **{date_str}**:")
            for emotion, count in emotions_count.items():
                st.markdown(f"    - {emotion}: {count}회")
        else:
            st.markdown(f"- **{date_str}**: 감정 발화 없음")

    # 시각화를 위한 데이터프레임 생성
    scatter_data = []
    for date_str in sorted_dates:
        emotions_count = Counter(daily_emotions[date_str])
        for emotion, count in emotions_count.items():
            for _ in range(count): # 감정 횟수만큼 데이터 포인트 추가
                scatter_data.append({'날짜': date_str, '감정': emotion})

    df_scatter = pd.DataFrame(scatter_data)

    # 감정별 색상 매핑
    emotion_colors = {
        '기쁨': 'green',
        '놀람': 'blue',
        '분노': 'red',
        '슬픔': 'purple',
        '두려움': 'orange'
    }

    # 날짜를 숫자로 변환하여 x축에 사용 (간격 유지를 위해)
    if not df_scatter.empty:
        df_scatter['날짜_num'] = df_scatter['날짜'].apply(lambda x: pd.to_datetime(x).toordinal())
        unique_dates_num = sorted(df_scatter['날짜_num'].unique())
        date_labels = [datetime.datetime.fromordinal(d).strftime('%Y-%m-%d') for d in unique_dates_num]

        fig1, ax1 = plt.subplots(figsize=(12, 6))

        for emotion, color in emotion_colors.items():
            subset = df_scatter[df_scatter['감정'] == emotion]
            if not subset.empty:
                ax1.scatter(subset['날짜_num'], [emotion] * len(subset), color=color, label=emotion, alpha=0.7, s=100)

        ax1.set_xlabel("날짜")
        ax1.set_ylabel("감정")
        ax1.set_title(f"{person_name}님의 일별 감정 산포도")
        ax1.set_xticks(unique_dates_num)
        ax1.set_xticklabels(date_labels, rotation=45, ha='right')
        ax1.legend(title="감정")
        ax1.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig1)
    else:
        st.info(f"{person_name}님의 발화에서 감정 데이터가 발견되지 않았습니다. (일별 산포도)")


    # --------------------------------------------------------------------------
    # 2. 주간 감정 변화 그래프 (가장 많이 등장한 감정)
    st.subheader(f"2. {person_name}님의 주간 감정 변화 그래프")

    st.markdown("""
    <div style="font-size: small; color: gray;">
        <p>이 그래프는 주간 동안 선택된 인물의 주요 감정 변화를 보여줍니다. 각 날짜의 대표 감정은 해당 일에 가장 많이 나타난 감정으로 선정됩니다.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**{person_name}님의 주간 주요 감정 변화:**")

    # 각 날짜별로 가장 많이 등장한 감정 추출 및 횟수 포함
    weekly_dominant_emotions = []
    for date_str in sorted_dates:
        emotions_list = daily_emotions[date_str] # 이미 위에서 daily_emotions에 Winter의 감정만 추출되어 있음
        
        if emotions_list:
            most_common_emotion, count = Counter(emotions_list).most_common(1)[0]
            weekly_dominant_emotions.append({'날짜': date_str, '주요 감정': most_common_emotion})
            st.markdown(f"- **{date_str}**: {most_common_emotion} ({count}회)")
        else:
            weekly_dominant_emotions.append({'날짜': date_str, '주요 감정': '감정 없음'})
            st.markdown(f"- **{date_str}**: 감정 발화 없음")

    df_weekly = pd.DataFrame(weekly_dominant_emotions)
    df_weekly['날짜'] = pd.to_datetime(df_weekly['날짜'])
    df_weekly = df_weekly.sort_values(by='날짜')

    # 감정 순서를 지정 (y축 순서)
    emotion_order = ['기쁨', '놀람', '분노', '슬픔', '두려움', '감정 없음']
    df_weekly['주요 감정_ordered'] = pd.Categorical(df_weekly['주요 감정'], categories=emotion_order, ordered=True)

    if not df_weekly.empty:
        fig2, ax2 = plt.subplots(figsize=(12, 6))

        # 각 감정에 따른 색상 매핑
        emotion_color_map = {
            '기쁨': 'lightgreen',
            '놀람': 'lightblue',
            '분노': 'salmon',
            '슬픔': 'mediumpurple',
            '두려움': 'gold',
            '감정 없음': 'lightgray'
        }

        # 그래프 그리기
        for i, row in df_weekly.iterrows():
            ax2.plot(row['날짜'], row['주요 감정_ordered'], 'o', 
                     color=emotion_color_map.get(row['주요 감정'], 'gray'), markersize=10)

        ax2.plot(df_weekly['날짜'], df_weekly['주요 감정_ordered'], color='gray', linestyle='--', alpha=0.5)

        ax2.set_xlabel("날짜")
        ax2.set_ylabel("주요 감정")
        ax2.set_title(f"{person_name}님의 주간 감정 변화")
        ax2.set_xticks(df_weekly['날짜'])
        ax2.set_xticklabels(df_weekly['날짜'].dt.strftime('%Y-%m-%d'), rotation=45, ha='right')
        ax2.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.info(f"{person_name}님의 발화에서 감정 데이터가 발견되지 않았습니다. (주간 변화 그래프)")