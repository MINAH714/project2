import streamlit as st
import requests
from datetime import date

# 나이 그룹별 상황 옵션
situations_by_age_group = {
    "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색"],
    "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발"],
    "adult_middle": ["가정", "직장생활", "건강 관리"],
    "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립"]
}

def age_group(age):
    if 13 <= age <= 19:
        return "teenager"
    elif 20 <= age <= 39:
        return "adult_young"
    elif 40 <= age <= 65:
        return "adult_middle"
    elif age > 65:
        return "senior"
    else:
        return "not_target"

st.title("AI 대화 더미데이터 생성기")

# 1. 파라미터 입력
name = st.selectbox("이름", ["Alice", "Peter", "Sue"])
age = st.number_input("나이", min_value=1, max_value=120, value=17)
gender = st.radio("성별", ["male", "female"])

group = age_group(age)
if group == "not_target":
    st.warning("13세 이상만 대상입니다.")
    st.stop()

situation_options = situations_by_age_group[group]
situation = st.selectbox("상황", situation_options)

timestamp = st.date_input("시작 날짜", value=date(2025, 6, 1))
step = st.number_input("Step(일)", min_value=1, max_value=30, value=3)
count = st.number_input("갯수", min_value=1, max_value=20, value=4)

# 2. 버튼 클릭 시 FastAPI로 요청
if st.button("더미데이터 생성 및 다운로드"):
    with st.spinner("데이터 생성 중..."):
        payload = {
            "name": name,
            "age": age,
            "gender": gender,
            "situation": situation,
            "timestamp": timestamp.strftime("%Y-%m-%d"),
            "step": int(step),
            "count": int(count)
        }
        # FastAPI 서버 주소에 맞게 수정하세요
        api_url = "http://localhost:8000/generate-dummy/"
        try:
            res = requests.post(api_url, json=payload)
            if res.status_code == 200 and "filename" in res.json():
                filename = res.json()["filename"]
                # 파일 다운로드
                download_url = f"http://localhost:8000/download/{filename}"
                file_res = requests.get(download_url)
                if file_res.status_code == 200:
                    # 다운로드 버튼 제공
                    st.success("파일 생성 완료! 아래 버튼으로 다운로드하세요.")
                    st.download_button(
                        label="JSON 파일 다운로드",
                        data=file_res.content,
                        file_name=filename,
                        mime="application/json"
                    )
                else:
                    st.error("파일 다운로드에 실패했습니다.")
            else:
                st.error("FastAPI 서버에서 에러가 발생했습니다.")
        except Exception as e:
            st.error(f"서버 요청 중 오류 발생: {e}")
