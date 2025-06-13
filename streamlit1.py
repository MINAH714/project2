import streamlit as st
import pandas as pd
import numpy as np
import json
import altair as alt

# 파스텔톤 감정 색상
EMOTION_COLORS = {
    "기쁨": "#FBA518",
    "분노": "#FF3F33",
    "슬픔": "#4DA8DA",
    "두려움": "#B771E5",
    "놀람": "#16C47F",
    "혐오": "#4C585B",
}

# 데이터 불러오기 (예시)
with open('emotion_test_random_data1.json', encoding='utf-8') as f:
    raw = json.load(f)

rows = []
for emotion, items in raw.items():
    for idx, item in enumerate(items):
        rows.append({
            "timestamp": item.get("timestamp", pd.Timestamp.now() - pd.Timedelta(hours=len(rows))),
            "emotion": emotion,
            "strength": item.get("strength", np.random.uniform(0.3, 1.0)),
            "content": item.get("content", "")
        })

df = pd.DataFrame(rows)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# ===== UI 꾸미기 =====
st.set_page_config(
    page_title="감정 분석 리포트",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 상단 컬러 헤더
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #FFF9B1 0%, #FFB3AB 20%, #A7C7E7 40%, #CAB8FF 60%, #B5EAD7 80%, #D3D3D3 100%);
                padding: 1.3rem 1rem 1rem 1rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: #444; margin-bottom: 0.5rem;">감정 변화 리포트</h1>
        <p style="color: #666; font-size:1.1rem;">채팅을 통한 감정의 세기와 변화 추이를 시각화합니다.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 사이드바: 감정별 색상 안내
with st.sidebar:
    st.header("감정별 색상 안내")
    for emotion, color in EMOTION_COLORS.items():
        st.markdown(
            f"<div style='display:flex; align-items:center; margin-bottom:6px;'>"
            f"<div style='width:18px; height:18px; background:{color}; border-radius:4px; margin-right:8px;'></div>"
            f"<span style='font-size:1.05rem;'>{emotion}</span></div>",
            unsafe_allow_html=True
        )
    st.markdown("---")
    st.info("상단 그래프는 채팅별 감정 산포도, 하단 그래프는 일주일간 감정 변화 추이를 보여줍니다.")

# 산포도 그래프
st.subheader("🟡 채팅별 감정 산포도")
scatter = alt.Chart(df).mark_circle(size=80).encode(
    x=alt.X('timestamp:T', title='시간'),
    y=alt.Y('strength:Q', title='감정 세기', scale=alt.Scale(domain=[0, 1])),
    color=alt.Color('emotion:N', scale=alt.Scale(domain=list(EMOTION_COLORS.keys()), range=list(EMOTION_COLORS.values()))),
    tooltip=['timestamp:T', 'emotion:N', 'strength:Q', 'content:N']
).properties(width=900, height=350).interactive()
st.altair_chart(scatter, use_container_width=True)

# 일주일 감정 변화 선그래프
st.subheader("🟦 일주일 감정 변화 추이")
one_week_ago = df['timestamp'].max() - pd.Timedelta(days=7)
week_df = df[df['timestamp'] >= one_week_ago].copy()
week_df['date'] = week_df['timestamp'].dt.date
pivot = week_df.pivot_table(index='date', columns='emotion', values='strength', aggfunc=np.mean)
pivot = pivot.reset_index().melt('date', var_name='emotion', value_name='strength')

line = alt.Chart(pivot).mark_line(point=True, strokeWidth=3).encode(
    x=alt.X('date:T', title='날짜'),
    y=alt.Y('strength:Q', title='감정 세기', scale=alt.Scale(domain=[0, 1])),
    color=alt.Color('emotion:N', scale=alt.Scale(domain=list(EMOTION_COLORS.keys()), range=list(EMOTION_COLORS.values()))),
    tooltip=['date:T', 'emotion:N', 'strength:Q']
).properties(width=900, height=350).interactive()
st.altair_chart(line, use_container_width=True)

# 하단 안내
st.markdown(
    """
    <div style="margin-top:2rem; color:#888; font-size:0.95rem;">
        <b>설명:</b> 산포도는 각 채팅별 감정 세기를, 선그래프는 일주일간 감정별 평균 세기 변화를 보여줍니다.<br>
        감정 색상은 파스텔톤으로 통일되어 시각적 편안함을 제공합니다.
    </div>
    """,
    unsafe_allow_html=True
)
