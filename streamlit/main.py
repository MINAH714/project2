from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random
import json
import httpx # Use httpx for async requests
from typing import Literal, List, Dict, Union, AsyncGenerator
from starlette.responses import StreamingResponse
import asyncio # Import asyncio for async operations
import os # For saving files

app = FastAPI()

origins = [
    "*", # Streamlit's default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions" # Ensure this is correct for your LM Studio setup

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

EMOTIONS = ["기쁨", "분노", "슬픔", "두려움", "놀람"]

class UserInput(BaseModel):
    person_name: str = Field(..., description="대화할 사람의 이름")
    age: int = Field(..., ge=13, description="대화 참여자의 나이 (13세 이상)")
    gender: Literal["male", "female"] = Field(..., description="대화 참여자의 성별")
    situation: str = Field(..., description="대화의 상황")
    start_timestamp: datetime = Field(datetime(2025, 6, 1), description="대화문 생성 기준 시작 타임스탬프 (기본값: 2025-06-01)")
    step_days: int = Field(..., ge=1, description="대화문 생성 간격 (일 단위)")
    num_conversations: int = Field(..., ge=1, description="생성할 대화문의 갯수")

def get_age_group(age: int) -> str:
    if 13 <= age <= 19:
        return "teenager"
    elif 20 <= age <= 39:
        return "adult_young"
    elif 40 <= age <= 65:
        return "adult_middle"
    elif age >= 66:
        return "senior"
    else:
        return "not_target"

def generate_prompt(
    person_name: str,
    age_group: str,
    gender: str,
    situation: str,
    conversation_length_minutes: int,
    current_date: str
) -> tuple[str, int]:
    num_utterances = random.randint(conversation_length_minutes * 10, conversation_length_minutes * 11)
    
    selected_emotion = random.choice(EMOTIONS) # 주된 감정 하나 선택

    prompt = f"""
    당신은 공감형 대화 생성 전문가 입니다. 아래 정보를 바탕으로 챗봇과 {person_name} 간의 자연스럽고 **다채로운 대화문**을 생성해주세요.
    **중복되는 대화 패턴이나 어조는 최대한 피하고, 창의적인 대화 흐름을 만들어 주세요.**

    ---
    **대화 정보:**
    - **참여자:** 챗봇과 {person_name}
    - **{person_name} 정보:**
        - **이름:** {person_name}
        - **나이:** {age_group} 그룹
        - **성별:** {gender}
    - **상황:** {situation}
    - **현재 날짜:** {current_date}
    - **대화 목표:** {person_name}과의 자연스러운 대화 흐름을 유지합니다.
    - **대화 길이:** 약 {conversation_length_minutes}분 (총 {num_utterances}개 내외의 발화)
    - **포함될 감정:** 이 대화의 주된 감정은 '{selected_emotion}'입니다. 대화 전반에 걸쳐 이 감정이 자연스럽게 드러나도록 해주세요. 하지만, 대화의 맥락과 흐름에 따라 **다른 감정들도 자연스럽게 나타날 수 있도록** 복합적인 감정 표현을 시도해주세요. 하나의 감정에만 고정되지 않도록 해주세요.

    ---
    **대화 형식:**
    각 발화는 '참여자: [내용] | 감정: [감정1], [감정2]' 형식으로 표현해주세요. 감정은 쉼표로 구분하여 여러 개를 표현할 수 있습니다. 
    5개의 감정을 순차적으로 표현해주세요.
    예시:
    사용자: 안녕하세요! 오늘 하루는 어떠셨어요? | 감정: 기쁨
    {person_name}: 아, 네. 그냥 그랬어요. 좀 피곤하네요. | 감정: 슬픔, 피곤

    ---
    **대화 시작:**
    사용자: 안녕하세요, {person_name}님. 요즘 {situation} 관련해서 어떠신지 궁금해서요.
    {person_name}:
    """
    return prompt, num_utterances

async def call_lm_studio_stream(prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "eeve-korean-instruct-10.8b-v1.0",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream("POST", LM_STUDIO_API_URL, headers=headers, json=payload, timeout=None) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    try:
                        chunk_str = chunk.decode("utf-8")
                        for line in chunk_str.splitlines():
                            if line.startswith("data: "):
                                json_data = line[len("data: "):]
                                if json_data.strip() == "[DONE]":
                                    continue
                                try:
                                    data = json.loads(json_data)
                                    if "choices" in data and data["choices"]:
                                        delta = data["choices"][0]["delta"]
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    print(f"Invalid JSON chunk from LM Studio: {json_data}")
                                    continue
                    except UnicodeDecodeError:
                        print(f"UnicodeDecodeError on chunk from LM Studio: {chunk}")
                        continue
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"LM Studio API 요청 중 오류 발생: {exc}. LM Studio 서버가 실행 중인지 확인해주세요.")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=500, detail=f"LM Studio API 응답 오류: {exc.response.status_code} - {exc.response.text}")

def parse_conversation_data(raw_text: str, person_name: str, total_utterances_expected: int) -> List[Dict]:
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
                        "emotions": emotions if emotions else [random.choice(EMOTIONS)]
                    })
            except Exception as e:
                print(f"Error parsing line: '{line}' - {e}")
                continue
    
    current_utterances = len(parsed_data)
    if current_utterances > total_utterances_expected * 1.5:
        parsed_data = parsed_data[:int(total_utterances_expected * 1.2)]
    elif current_utterances < total_utterances_expected * 0.5:
        if parsed_data:
            while len(parsed_data) < total_utterances_expected * 0.8:
                parsed_data.extend(random.sample(parsed_data, k=min(len(parsed_data), 5)))

    return parsed_data

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Empathy Conversation Generator API (FastAPI Server)!"}

@app.post("/generate-stream/")
async def generate_conversation_stream_endpoint(user_input: UserInput):
    async def generate_chunks():
        person_name = user_input.person_name
        age = user_input.age
        gender = user_input.gender
        situation = user_input.situation
        start_timestamp = user_input.start_timestamp
        step_days = user_input.step_days
        num_conversations = user_input.num_conversations
        age_group = get_age_group(age)

        yield json.dumps({"status": "generating", "message": "대화 생성을 시작합니다..."}, ensure_ascii=False) + "\n"

        for i in range(num_conversations):
            current_date = start_timestamp + timedelta(days=i * step_days)
            formatted_date = current_date.strftime("%Y-%m-%d")

            conversation_length_minutes = random.randint(5, 10)
            prompt, total_expected_utterances = generate_prompt(
                person_name, age_group, gender, situation, conversation_length_minutes, formatted_date
            )
            
            max_tokens_for_lm = total_expected_utterances * 50 

            full_lm_response_content = ""
            try:
                async for content_chunk in call_lm_studio_stream(prompt, max_tokens_for_lm):
                    full_lm_response_content += content_chunk
            except HTTPException as e:
                yield json.dumps({"status": "error", "message": str(e.detail)}, ensure_ascii=False) + "\n"
                return
            except Exception as e:
                yield json.dumps({"status": "error", "message": f"LM Studio 응답 처리 중 오류 발생: {e}"}, ensure_ascii=False) + "\n"
                return

            parsed_conversation = parse_conversation_data(full_lm_response_content, person_name, total_expected_utterances)
            
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

        yield json.dumps({"status": "complete", "message": "모든 대화 생성이 완료되었습니다."}, ensure_ascii=False) + "\n"

    return StreamingResponse(generate_chunks(), media_type="application/x-ndjson")

@app.post("/save-conversations/")
async def save_conversations(data: Dict[str, List[Dict]]):
    """
    Save the generated conversation data to a JSON file on the server.
    """
    if "data" not in data or not isinstance(data["data"], list):
        raise HTTPException(status_code=400, detail="Invalid data format. Expected a list under 'data' key.")

    generated_data = data["data"]
    if not generated_data:
        raise HTTPException(status_code=400, detail="No conversation data to save.")

    first_entry = generated_data[0]
    person_name = first_entry.get("person_name", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"dialogue_report_{person_name}_{timestamp}.json"
    
    save_directory = "generated_dialogues"
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, file_name)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(generated_data, f, ensure_ascii=False, indent=2)
        return {"message": "대화 데이터가 성공적으로 저장되었습니다.", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류 발생: {e}")

@app.post("/save-user-utterances/")
async def save_user_utterances(data: Dict[str, List[Dict]]):
    """
    Extracts only the specified user's utterances and saves them to a JSON file.
    """
    if "data" not in data or not isinstance(data["data"], list):
        raise HTTPException(status_code=400, detail="Invalid data format. Expected a list under 'data' key.")

    generated_data = data["data"]
    if not generated_data:
        raise HTTPException(status_code=400, detail="No conversation data to process.")

    user_utterances_data = []
    person_name = "unknown" # Default if not found

    for entry in generated_data:
        if "person_name" in entry:
            person_name = entry["person_name"]
        
        if "conversation" in entry and isinstance(entry["conversation"], list):
            for utterance in entry["conversation"]:
                if utterance.get("speaker") == person_name:
                    user_utterances_data.append({
                        "timestamp": entry.get("timestamp"),
                        "speaker": utterance.get("speaker"),
                        "content": utterance.get("content"),
                        "emotions": utterance.get("emotions", [])
                    })

    if not user_utterances_data:
        raise HTTPException(status_code=404, detail="No utterances found for the specified person.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"user_utterances_report_{person_name}_{timestamp}.json"
    
    save_directory = "generated_dialogues"
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, file_name)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_utterances_data, f, ensure_ascii=False, indent=2)
        return {"message": "사용자 발화 데이터가 성공적으로 저장되었습니다.", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류 발생: {e}")


@app.get("/get_situation_options/")
async def get_situation_options(age: int):
    age_group = get_age_group(age)
    if age_group in SITUATION_OPTIONS:
        return {"situation_options": SITUATION_OPTIONS[age_group]}
    return {"situation_options": []}