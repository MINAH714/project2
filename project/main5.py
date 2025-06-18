from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어 추가
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random
import json
import requests
from typing import Literal, List, Dict, Union

app = FastAPI()

# CORS 설정: Streamlit 앱이 FastAPI 서버에 접근할 수 있도록 허용
# 실제 배포 시에는 특정 도메인으로 제한하는 것이 좋습니다.
origins = [
    "http://localhost",
    "http://localhost:8501", # Streamlit 기본 포트
    # 필요한 경우 여기에 Streamlit 앱의 다른 호스트/포트 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LM Studio 모델의 API 엔드포인트 (기본값, 필요에 따라 수정)
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions" # LM Studio 기본 포트

# 나이 그룹 정의
AGE_GROUPS = {
    "teenager": (13, 19),
    "adult_young": (20, 39),
    "adult_middle": (40, 65),
    "senior": (66, 150) # 65세 이상으로 변경
}

# 상황 정의 (나이 그룹별)
SITUATION_OPTIONS = {
    "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색"],
    "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발"],
    "adult_middle": ["가정", "직장생활", "건강 관리"],
    "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립"]
}

# 정의된 감정
EMOTIONS = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]

class UserInput(BaseModel):
    person_name: Literal["Alice", "Peter", "Sue"] = Field(..., description="대화할 사람의 이름")
    age: int = Field(..., ge=13, description="대화 참여자의 나이 (13세 이상)")
    gender: Literal["male", "female"] = Field(..., description="대화 참여자의 성별")
    situation: str = Field(..., description="대화의 상황")
    start_timestamp: datetime = Field(datetime(2025, 6, 1), description="대화문 생성 기준 시작 타임스탬프 (기본값: 2025-06-01)")
    step_days: int = Field(..., ge=1, description="대화문 생성 간격 (일 단위)")
    num_conversations: int = Field(..., ge=1, description="생성할 대화문의 갯수")

def get_age_group(age: int) -> str:
    """나이에 따른 연령대 반환"""
    if 13 <= age <= 19:
        return "teenager"
    elif 20 <= age <= 39:
        return "adult_young"
    elif 40 <= age <= 65:
        return "adult_middle"
    else: # 65세 이상
        return "senior"

def generate_prompt(
    person_name: str,
    age: int,
    gender: str,
    situation: str,
    conversation_length_minutes: int,
    current_date: str
) -> str:
    """LM Studio 모델에 전달할 프롬프트 생성"""
    num_utterances = random.randint(conversation_length_minutes * 10, conversation_length_minutes * 11)
    
    # 감정의 다양성을 높이기 위해 초기 감정 분포를 랜덤하게 설정
    initial_emotions = random.sample(EMOTIONS, k=random.randint(2, min(len(EMOTIONS), 4)))
    initial_emotion_str = ", ".join(initial_emotions) if initial_emotions else "다양한 감정"

    prompt = f"""
    당신은 공감형 대화 생성 챗봇입니다. 아래 정보를 바탕으로 사용자(챗봇)와 {person_name} 간의 자연스러운 대화문을 생성해주세요.

    ---
    **대화 정보:**
    - **참여자:** 사용자(챗봇)와 {person_name}
    - **{person_name} 정보:**
        - **이름:** {person_name}
        - **나이:** {age}세 ({get_age_group(age)} 그룹)
        - **성별:** {gender}
    - **상황:** {situation}
    - **현재 날짜:** {current_date}
    - **대화 목표:** {person_name}의 감정을 이해하고 공감하며, 자연스러운 대화 흐름을 유지합니다.
    - **대화 길이:** 약 {conversation_length_minutes}분 (총 {num_utterances}개 내외의 발화)
    - **포함될 감정:** {EMOTIONS} 중 적어도 {initial_emotion_str}을(를) 포함하며, 대화 흐름에 따라 자연스럽게 여러 감정이 나타나도록 해주세요. 하나의 감정에 고정되지 않고, 대화 중간에 감정이 변화하는 것처럼 보이도록 생성해주세요.

    ---
    **대화 형식:**
    각 발화는 '참여자: [내용] | 감정: [감정1], [감정2]' 형식으로 표현해주세요. 감정은 쉼표로 구분하여 여러 개를 표현할 수 있습니다. 
    최소 1개에서 최대 3개의 감정을 표현해주세요.
    예시:
    사용자: 안녕하세요! 오늘 하루는 어떠셨어요? | 감정: 기쁨
    {person_name}: 아, 네. 그냥 그랬어요. 좀 피곤하네요. | 감정: 슬픔, 피곤

    ---
    **대화 시작:**
    사용자: 안녕하세요, {person_name}님. 요즘 {situation} 관련해서 어떠신지 궁금해서요.
    {person_name}:
    """
    return prompt, num_utterances

def call_lm_studio(prompt: str, max_tokens: int) -> str:
    """LM Studio API 호출 및 응답 반환"""
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "eeve-korean-instruct-10.8b-v1.0", # 사용하려는 모델명
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    try:
        response = requests.post(LM_STUDIO_API_URL, headers=headers, json=data, timeout=300) # 타임아웃 5분
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        completion = response.json()
        return completion["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"LM Studio API 호출 오류: {e}. LM Studio 서버가 실행 중인지 확인해주세요 (http://localhost:1234).")

def parse_conversation_data(raw_text: str, person_name: str, total_utterances: int) -> List[Dict]:
    """LM Studio 응답 텍스트를 파싱하여 JSON 형식으로 변환"""
    parsed_data = []
    lines = raw_text.strip().split('\n')
    
    for line in lines:
        if ':' in line and '|' in line:
            try:
                parts = line.split('|')
                speaker_content = parts[0].strip()
                emotion_content = parts[1].strip()

                speaker_name, content = speaker_content.split(':', 1)
                speaker_name = speaker_name.strip()
                content = content.strip()

                emotions_str = emotion_content.replace('감정:', '').strip()
                emotions = [e.strip() for e in emotions_str.split(',') if e.strip() in EMOTIONS]

                if speaker_name in ["사용자", person_name]:
                    parsed_data.append({
                        "speaker": speaker_name,
                        "content": content,
                        "emotions": emotions if emotions else [random.choice(EMOTIONS)] # 감정 없으면 랜덤 감정 추가
                    })
            except Exception:
                pass # 잘못된 형식의 줄은 건너뛰기
    
    # 생성된 발화 수가 너무 적거나 많을 경우 조절 (단순히 잘라내거나 반복)
    if len(parsed_data) > total_utterances * 1.5:
        parsed_data = parsed_data[:int(total_utterances * 1.2)]
    elif len(parsed_data) < total_utterances * 0.5:
        if parsed_data:
            while len(parsed_data) < total_utterances * 0.8:
                parsed_data.extend(random.sample(parsed_data, k=min(len(parsed_data), 5)))

    return parsed_data

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Empathy Conversation Generator API (FastAPI Server)!"}

@app.post("/generate_conversation/")
async def generate_conversation_endpoint(user_input: UserInput):
    person_name = user_input.person_name
    age = user_input.age
    gender = user_input.gender
    situation = user_input.situation
    start_timestamp = user_input.start_timestamp
    step_days = user_input.step_days
    num_conversations = user_input.num_conversations

    all_conversation_data = []

    for i in range(num_conversations):
        current_date = start_timestamp + timedelta(days=i * step_days)
        formatted_date = current_date.strftime("%Y-%m-%d")

        conversation_length_minutes = random.randint(5, 10) # 5분-10분 랜덤
        prompt, total_expected_utterances = generate_prompt(
            person_name, age, gender, situation, conversation_length_minutes, formatted_date
        )
        
        max_tokens_for_lm = total_expected_utterances * 30 

        try:
            raw_lm_response = call_lm_studio(prompt, max_tokens_for_lm)
            parsed_conversation = parse_conversation_data(raw_lm_response, person_name, total_expected_utterances)
            
            all_conversation_data.append({
                "timestamp": formatted_date,
                "person_name": person_name,
                "age": age,
                "gender": gender,
                "situation": situation,
                "conversation_length_minutes": conversation_length_minutes,
                "total_utterances_expected": total_expected_utterances,
                "total_utterances_generated": len(parsed_conversation),
                "conversation": parsed_conversation
            })
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"대화 생성 중 오류 발생: {e}")

    # JSON 파일로 다운로드할 수 있도록 응답 (Streamlit에서 처리)
    json_output = json.dumps(all_conversation_data, indent=4, ensure_ascii=False)
    
    # Streamlit에서 직접 파일을 다운로드할 수 있도록 JSON 데이터를 반환
    return Response(content=json_output, media_type="application/json")


# 상황 옵션을 동적으로 가져오는 엔드포인트
@app.get("/get_situation_options/")
async def get_situation_options(age: int):
    age_group = get_age_group(age)
    if age_group in SITUATION_OPTIONS:
        return {"situation_options": SITUATION_OPTIONS[age_group]}
    return {"situation_options": []}