import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

# ====== 감정별 파스텔톤 색상 ======
EMOTION_COLORS = {
    "기쁨": "#FBA518",
    "분노": "#FF3F33",
    "슬픔": "#4DA8DA",
    "두려움": "#B771E5",
    "놀람": "#16C47F",
    "혐오": "#4C585B",
}

# ====== 산포도 데이터: 감정 한쪽에 몰리게 ======
np.random.seed(42)
num_points = 50
emotions = list(EMOTION_COLORS.keys())
# '기쁨'과 '놀람'에 높은 확률
weights = [0.4, 0.1, 0.1, 0.1, 0.2, 0.1]
chosen_emotions = np.random.choice(emotions, size=num_points, p=weights)
base_time = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)
timestamps = [base_time + timedelta(minutes=5*i) for i in range(num_points)]
strengths = np.random.uniform(0.3, 1.0, size=num_points)
scatter_df = pd.DataFrame({
    "timestamp": timestamps,
    "emotion": chosen_emotions,
    "strength": strengths
})

# ====== 선그래프 데이터: 감정 세기 들쭉날쭉 ======
days = 7
dates = [datetime.now().date() - timedelta(days=i) for i in range(days-1, -1, -1)]
records = []
for date in dates:
    for emotion in emotions:
        # 감정별로 변동폭 크게 (들쭉날쭉)
        strength = np.clip(np.random.normal(loc=0.6, scale=0.25), 0.1, 1.0)
        records.append({
            "date": date,
            "weekday": pd.Timestamp(date).strftime('%a'),
            "emotion": emotion,
            "strength": strength
        })
line_df = pd.DataFrame(records)

# ====== UI ======
st.set_page_config(
    page_title="감정 분석 리포트",
    page_icon="🧠",
    layout="wide"
)

st.markdown(
    """
    <div style="background: linear-gradient(90deg, #FFF9B1 0%, #FFB3AB 20%, #A7C7E7 40%, #CAB8FF 60%, #B5EAD7 80%, #D3D3D3 100%);
                padding: 1.3rem 1rem 1rem 1rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: #444; margin-bottom: 0.5rem;">감정 변화 리포트</h1>
        <p style="color: #666; font-size:1.1rem;">감정 분포와 일주일간 감정 변화 추이를 시각화합니다.</p>
    </div>
    """,
    unsafe_allow_html=True
)

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

# ====== 1. 채팅별 감정 산포도 ======
st.subheader("🟡 채팅별 감정 산포도")
scatter = alt.Chart(scatter_df).mark_circle(size=80).encode(
    x=alt.X('timestamp:T', title='시간'),
    y=alt.Y('strength:Q', title='감정 세기', scale=alt.Scale(domain=[0, 1])),
    color=alt.Color('emotion:N', scale=alt.Scale(domain=emotions, range=list(EMOTION_COLORS.values()))),
    tooltip=['timestamp:T', 'emotion:N', 'strength:Q']
).properties(width=900, height=350).interactive()
st.altair_chart(scatter, use_container_width=True)

# ====== 2. 일주일 감정 변화 선그래프 ======
st.subheader("🟦 일주일 감정 변화 추이")
line = alt.Chart(line_df).mark_line(point=True, strokeWidth=3).encode(
    x=alt.X('date:T', title='날짜'),
    y=alt.Y('strength:Q', title='감정 세기', scale=alt.Scale(domain=[0, 1])),
    color=alt.Color('emotion:N', scale=alt.Scale(domain=emotions, range=list(EMOTION_COLORS.values()))),
    tooltip=['date:T', 'weekday:N', 'emotion:N', 'strength:Q']
).properties(width=900, height=350).interactive()
st.altair_chart(line, use_container_width=True)

st.markdown(
    """
    <div style="margin-top:2rem; color:#888; font-size:0.95rem;">
        <b>설명:</b> 산포도는 감정 분포가 한쪽에 몰려있는 형태로, 선그래프는 감정 세기가 들쭉날쭉하게 변동합니다.<br>
        감정 색상은 파스텔톤으로 통일되어 시각적 편안함을 제공합니다.
    </div>
    """,
    unsafe_allow_html=True
)
