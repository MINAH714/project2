import streamlit3 as st
import pandas as pd
import altair as alt
from pathlib import Path

DATA_FILES = {
    "청소년 여성": "adolescent_female_daily.json",
    "성인 남성": "adult_male_daily.json",
    "노년 남성": "elderly_male_daily.json"
}

st.sidebar.title("데이터 선택")
selected_label = st.sidebar.selectbox(
    "분석할 집단을 선택하세요",
    list(DATA_FILES.keys())
)
selected_file = DATA_FILES[selected_label]

def load_json_data(file_path):
    try:
        df = pd.read_json(file_path)
    except ValueError:
        df = pd.read_json(file_path, lines=True)
    return df

data_path = Path(__file__).parent / selected_file
df = load_json_data(data_path)

st.header(f"{selected_label} 감정 데이터 분석")

emotion_count = df["emotion"].value_counts().reset_index()
emotion_count.columns = ["emotion", "count"]

bar_chart = alt.Chart(emotion_count).mark_bar().encode(
    x=alt.X("emotion:N", title="감정"),
    y=alt.Y("count:Q", title="빈도"),
    color="emotion:N"
).properties(width=600, height=350)
st.altair_chart(bar_chart, use_container_width=True)

if "date" in df.columns:
    line_df = df.groupby(["date", "emotion"]).size().reset_index(name="count")
    line_chart = alt.Chart(line_df).mark_line(point=True).encode(
        x="date:T",
        y="count:Q",
        color="emotion:N",
        tooltip=["date:T", "emotion:N", "count:Q"]
    ).properties(width=600, height=350)
    st.altair_chart(line_chart, use_container_width=True)
