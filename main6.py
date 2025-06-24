from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random
import json
import requests
from typing import Literal, List, Dict, Union, AsyncGenerator
from starlette.responses import StreamingResponse, FileResponse
import os
import uvicorn # uvicorn 임포트 추가 (개발 시 실행용)

app = FastAPI()

# --- Configuration ---
origins = [
    "http://localhost",
    "http://localhost:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
OUTPUT_DIR = "generated_dialogues" # 저장 폴더 상수화
os.makedirs(OUTPUT_DIR, exist_ok=True) # 폴더 없으면 생성

AGE_GROUPS = {
    "teenager": (13, 19),
    "adult_young": (20, 39),
    "adult_middle": (40, 65),
    "senior": (66, 150)
}

SITUATION_OPTIONS = {
    "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색", "일상 생활"],
    "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발", "일상 생활"],
    "adult_middle": ["가정", "직장생활", "건강 관리", "일상 생활"],
    "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립", "일상 생활"]
}

EMOTIONS = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]

# --- Pydantic Models ---
class UserInput(BaseModel):
    person_name: str = Field("Alice", description="대화할 사람의 이름 (예: Alice, Peter, Sue 또는 다른 이름)")
    age: int = Field(..., ge=13, description="대화 참여자의 나이 (13세 이상)")
    gender: Literal["male", "female"] = Field(..., description="대화 참여자의 성별")
    situation: str = Field(..., description="대화의 상황")
    start_timestamp: datetime = Field(datetime(2025, 6, 1), description="대화문 생성 기준 시작 타임스탬프 (기본값: 2025-06-01)")
    step_days: int = Field(..., ge=1, description="대화문 생성 간격 (일 단위)")
    num_conversations: int = Field(..., ge=1, description="생성할 대화문의 갯수")

class SaveRequest(BaseModel):
    data: List[Dict] # 저장할 대화 데이터 리스트

# --- Helper Functions ---
def get_age_group(age: int) -> str:
    if 13 <= age <= 19:
        return "teenager"
    elif 20 <= age <= 39:
        return "adult_young"
    elif 40 <= age <= 65:
        return "adult_middle"
    else:
        return "senior"

def generate_prompt(
    person_name: str,
    age: int,
    gender: str,
    situation: str,
    conversation_length_minutes: int,
    current_date: str
) -> str:
    num_utterances = random.randint(conversation_length_minutes * 10, conversation_length_minutes * 11)
    
    prompt = f"""
    당신은 공감형 대화 생성 챗봇입니다. 아래 정보에 따라 사용자(챗봇)와 {person_name} 간의 자연스러운 대화를 생성해주세요.
    대화의 각 발화에는 **반드시 가장 적절한 감정 1개만 포함**하여 괄호 안에 명시해야 합니다. 감정은 한국어로 표현해야 합니다.

    ---
    **정보:**
    - 참여자: 사용자(챗봇), {person_name} ({age}세, {gender}, {get_age_group(age)} 그룹)
    - 상황: {situation}
    - 날짜: {current_date}
    - 대화 길이: 약 {conversation_length_minutes}분 ({num_utterances}개 발화 내외, 이 길이에 맞춰 대화를 자연스럽게 종료해주세요.)
    - **사용 가능한 감정 (이 목록 내에서만 선택):** {', '.join(EMOTIONS)}
    - **대화 흐름에 따라 자연스럽게 감정 변화를 반영해주세요.**

    ---
    **출력 형식 (반드시 이 형식을 따르세요):**
    각 발화는 '참여자: [내용] (감정: [감정])' 형식으로 작성합니다.
    **예시:**
    사용자: 안녕하세요! 오늘 하루는 어떠셨어요? (감정: 기쁨)
    {person_name}: 아, 네. 그냥 그랬어요. 좀 피곤하네요. (감정: 슬픔)
    사용자: 힘든 일이 있으셨군요. 제가 도와드릴 부분이 있을까요? (감정: 걱정)
    {person_name}: 아니요, 괜찮아요. 그냥 좀 쉬고 싶어요. (감정: 지침)
    사용자: 그럼 잠시 쉬면서 편안한 시간을 보내세요. (감정: 위로)
"""
    return prompt, num_utterances

def call_lm_studio(prompt: str, max_tokens: int) -> str:
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "eeve-korean-instruct-10.8b-v1.0",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    try:
        response = requests.post(LM_STUDIO_API_URL, headers=headers, json=data, timeout=900)
        response.raise_for_status()
        completion = response.json()
        return completion["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"LM Studio API 호출 오류: {e}. LM Studio 서버가 실행 중인지 확인해주세요 (http://localhost:1234).")

def parse_conversation_data(raw_text: str, person_name: str, total_utterances: int) -> List[Dict]:
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
                    # 사용자의 "분노" 감정 할당을 "기쁨"으로 변경
                    if speaker_name == "사용자" and "분노" in emotions:
                        emotions = ["기쁨"] 
                    parsed_data.append({
                        "speaker": speaker_name,
                        "content": content,
                        "emotions": emotions if emotions else [random.choice(EMOTIONS)]
                    })
            except Exception:
                pass
    
    if len(parsed_data) > total_utterances * 1.5:
        parsed_data = parsed_data[:int(total_utterances * 1.2)]
    elif len(parsed_data) < total_utterances * 0.5:
        if parsed_data:
            while len(parsed_data) < total_utterances * 0.8:
                parsed_data.extend(random.sample(parsed_data, k=min(len(parsed_data), 5)))

    return parsed_data

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Empathy Conversation Generator API (FastAPI Server)!"}

@app.post("/generate-stream/")
async def generate_conversation_stream_endpoint(user_input: UserInput):
    """
    사용자 입력에 따라 대화 데이터를 스트리밍 방식으로 생성하여 반환합니다.
    각 대화는 뉴라인으로 구분된 JSON 객체(NDJSON)로 전송됩니다.
    """
    async def generate_chunks():
        person_name = user_input.person_name
        age = user_input.age
        gender = user_input.gender
        situation = user_input.situation
        start_timestamp = user_input.start_timestamp
        step_days = user_input.step_days
        num_conversations = user_input.num_conversations

        yield json.dumps({"status": "generating", "message": "대화 생성을 시작합니다..."}, ensure_ascii=False) + "\n"

        for i in range(num_conversations):
            current_date = start_timestamp + timedelta(days=i * step_days)
            formatted_date = current_date.strftime("%Y-%m-%d")

            conversation_length_minutes = random.randint(5, 10)
            prompt, total_expected_utterances = generate_prompt(
                person_name, age, gender, situation, conversation_length_minutes, formatted_date
            )
            
            max_tokens_for_lm = total_expected_utterances * 30 

            try:
                raw_lm_response = call_lm_studio(prompt, max_tokens_for_lm)
                parsed_conversation = parse_conversation_data(raw_lm_response, person_name, total_expected_utterances)
                
                conversation_data_chunk = {
                    "timestamp": formatted_date,
                    "person_name": person_name,
                    "age": age,
                    "gender": gender,
                    "situation": situation,
                    "conversation_length_minutes": conversation_length_minutes,
                    "total_utterances_expected": total_expected_utterances,
                    "total_utterances_generated": len(parsed_conversation),
                    "conversation": parsed_conversation
                }
                
                yield json.dumps(conversation_data_chunk, ensure_ascii=False) + "\n"
                yield json.dumps({"status": "progress", "message": f"날짜 {formatted_date} 대화 생성 완료."}, ensure_ascii=False) + "\n"

            except HTTPException as e:
                yield json.dumps({"status": "error", "message": str(e.detail)}, ensure_ascii=False) + "\n"
                return
            except Exception as e:
                yield json.dumps({"status": "error", "message": f"대화 생성 중 오류 발생: {e}"}, ensure_ascii=False) + "\n"
                return
        
        yield json.dumps({"status": "complete", "message": "모든 대화 생성이 완료되었습니다."}, ensure_ascii=False) + "\n"

    return StreamingResponse(generate_chunks(), media_type="application/x-ndjson")

@app.get("/situation-options/")
async def get_situation_options(age: int):
    """
    주어진 나이에 해당하는 대화 상황 옵션을 반환합니다.
    """
    age_group = get_age_group(age)
    if age_group in SITUATION_OPTIONS:
        return {"situation_options": SITUATION_OPTIONS[age_group]}
    return {"situation_options": []}

@app.post("/save-conversations/")
async def save_conversations_to_file(request: SaveRequest):
    """
    클라이언트로부터 받은 대화 데이터를 JSON 파일로 저장합니다.
    """
    data = request.data
    if not data:
        raise HTTPException(status_code=400, detail="저장할 데이터가 없습니다.")

    try:
        # 첫 번째 대화의 정보로 파일 이름 생성 (기존 로직 유지)
        first_conversation = data[0]
        person_name = first_conversation.get("person_name", "unknown")
        timestamp = first_conversation.get("timestamp", datetime.now().strftime("%Y%m%d"))
        
        file_name = f"dialogue_report_with_emotions_{person_name}_{timestamp.replace('-', '')}.json"
        file_path = os.path.join(OUTPUT_DIR, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"message": f"대화 데이터가 '{file_path}'에 성공적으로 저장되었습니다.", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류 발생: {e}")

# 개발 시 편리하게 실행
if __name__ == "__main__":
    uvicorn.run("main6:app", host="0.0.0.0", port=8000, reload=True)