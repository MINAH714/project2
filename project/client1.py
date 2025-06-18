import streamlit as st
import requests
import json
import random
from datetime import date

# 입력 폼
st.title("AI 공감형 대화문 생성기")

name = st.selectbox("이름", ["Alice", "Peter", "Sue"])
age = st.number_input("나이", min_value=13, max_value=100, value=17)
gender = st.radio("성별", ["male", "female"])
situation_options = {
    "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색"],
    "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발"],
    "adult_middle": ["가정", "직장생활", "건강 관리"],
    "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립"]
}
def age_group(age):
    if 13 <= age <= 19: return "teenager"
    elif 20 <= age <= 39: return "adult_young"
    elif 40 <= age <= 65: return "adult_middle"
    elif age > 65: return "senior"
    else: return "not_target"
group = age_group(age)
situation = st.selectbox("상황", situation_options[group])

minutes = random.uniform(5, 10)
dialogue_count = random.randint(int(minutes * 10), int(minutes * 11))
today = date.today().strftime("%Y-%m-%d")

if st.button("AI 대화문 생성"):
    # 프롬프트 생성
    prompt = (
        f"이름: {name}, 나이: {age}, 성별: {gender}, 상황: {situation}, 날짜: {today}\n"
        f"{minutes:.1f}분 동안의 감정 공감형 대화문 {dialogue_count}개를 생성해줘. "
        "각 대화문은 1~2문장으로, 자연스럽고 현실적으로 만들어줘. "
        "각 대화문은 json 배열로 반환해줘. 예시: [\"대화1\", \"대화2\", ...]"
    )
    # LM Studio API 호출 예시 (포트/모델명 환경에 맞게 수정)
    api_url = "http://localhost:1234/v1/completions"
    headers = {"Content-Type": "application/json"}
    body = {
        "model": "eeve-korean-instruct-10.8b-v1.0",
        "prompt": prompt,
        "max_tokens": 2048,
        "temperature": 0.7,
        "stop": None
    }
    res = requests.post(api_url, headers=headers, json=body)
    result = res.json()
    try:
        text = result['choices'][0]['text']
        dialogues = json.loads(text)
    except Exception:
        dialogues = [text]
    # 대화문 중 한 개만 랜덤 선택
    one_dialogue = random.choice(dialogues) if isinstance(dialogues, list) and dialogues else dialogues[0]
    # 결과 출력
    st.subheader("생성된 대화문")
    st.write(one_dialogue)
    # JSON 저장 및 다운로드 버튼
    output = {
        "name": name,
        "age": age,
        "gender": gender,
        "situation": situation,
        "date": today,
        "dialogue": one_dialogue
    }
    json_str = json.dumps(output, ensure_ascii=False, indent=2)
    st.download_button("JSON 파일 다운로드", data=json_str, file_name="dialogue.json", mime="application/json")
