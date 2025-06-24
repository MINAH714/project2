from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field, validator
from typing import Literal
from datetime import datetime, timedelta
import httpx
import json
import os
import random
import uuid

# FastAPI 앱 인스턴스 생성
app = FastAPI()

# --- 설정 및 초기화 ---

# LM Studio API 설정
# LM Studio를 실행하고 모델 로드 후 "Start Server"를 클릭해야 합니다.
# LM Studio API의 기본 URL이 다를 경우 이 값을 수정해주세요.
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# 생성된 JSON 파일을 저장할 디렉토리 설정
# 스크립트 실행 위치에 'generated_conversations' 폴더가 생성됩니다.
OUTPUT_DIR = "generated_conversations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Pydantic 모델 정의 (POST 요청 유효성 검사용) ---

class ConversationRequest(BaseModel):
    """
    POST 요청 바디의 유효성을 검사하기 위한 Pydantic 모델.
    대화 생성에 필요한 파라미터들을 정의합니다.
    """
    person_name: str = Field(..., description="대화의 주인공 이름 (텍스트)")
    age: int = Field(..., ge=13, description="나이 (숫자, 13세 이상)")
    gender: Literal["male", "female"] = Field(..., description="성별 (male 또는 female)")
    situation: str = Field(..., description="원하는 컨셉의 대화 상황 (텍스트)")
    
    # 대화 시작 기준일은 2024년 6월 1일로 기본값 설정
    start_date: datetime = Field(
        datetime(2024, 6, 1), description="대화 시작 기준일 (YYYY-MM-DD)"
    )
    step_days: int = Field(..., ge=1, description="대화 간격 (일, 숫자)")
    num_conversations: int = Field(..., ge=1, description="생성할 대화문의 총 개수 (숫자)")

    @validator("age")
    def validate_age_group(cls, v):
        """1-12세는 대화 대상이 아니므로 유효성 검사를 수행합니다."""
        if 1 <= v <= 12:
            raise ValueError("1-12세는 너무 어려서 대상이 아닙니다. 13세 이상만 가능합니다.")
        return v

# --- 헬퍼 함수 정의 ---

def get_age_group(age: int) -> str:
    """나이를 기반으로 해당 연령대 그룹 문자열을 반환합니다."""
    if 13 <= age <= 19:
        return "teenager"
    elif 20 <= age <= 39:
        return "adult_young"
    elif 40 <= age <= 65:
        return "adult_middle"
    elif age >= 66:
        return "senior"
    return "unknown" # 이 코드는 validate_age_group에 의해 도달하지 않아야 합니다.

def generate_prompt(
    person_name: str,
    age_group: str,
    gender: str,
    situation: str,
    conversation_length_minutes: int,
) -> str:
    """
    LM Studio 모델에 전달할 프롬프트를 동적으로 생성합니다.
    대화의 길이, 감정 종류, 출력 형식을 포함합니다.
    """
    emotions = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]
    # 1분당 10~11개 대화문 기준으로 전체 대화문 개수를 랜덤으로 지정합니다.
    num_dialogues = random.randint(
        conversation_length_minutes * 10, conversation_length_minutes * 11
    )

    prompt = f"""
    당신은 {person_name}이라는 사용자와 대화하는 챗봇입니다.
    사용자는 {age_group} 연령대의 {gender}이며, 현재 '{situation}' 상황에 있습니다.
    다음 대화에서 사용자와 챗봇의 대화문을 총 {num_dialogues}개 생성해주세요.
    각 대화문에는 '사용자' 또는 '챗봇'의 발화자와 함께 다음 6가지 감정 중 하나를 반드시 포함해야 합니다: {', '.join(emotions)}.
    대화는 자연스럽고 맥락에 맞게 진행되어야 합니다.
    대화 내용을 JSON 배열 형태로 출력해주세요. 각 대화 객체는 'speaker', 'emotion', 'text' 키를 포함해야 합니다.
    예시:
    [
        {{ "speaker": "사용자", "emotion": "기쁨", "text": "안녕하세요!" }},
        {{ "speaker": "챗봇", "emotion": "놀람", "text": "안녕하세요, 만나서 반갑습니다!" }},
        ...
    ]
    """
    return prompt

async def process_conversation_request(
    person_name: str,
    age: int,
    gender: Literal["male", "female"],
    situation: str,
    start_date: datetime,
    step_days: int,
    num_conversations: int
):
    """
    대화 생성 및 LM Studio API 호출, JSON 파일 저장을 처리하는 핵심 공통 함수입니다.
    POST와 GET 엔드포인트 모두 이 함수를 호출하여 로직 중복을 방지합니다.
    """
    try:
        # 나이 유효성 검사 (GET 요청 시 Pydantic 모델을 통하지 않으므로 수동 적용)
        if 1 <= age <= 12:
            raise ValueError("1-12세는 너무 어려서 대상이 아닙니다. 13세 이상만 가능합니다.")

        age_group = get_age_group(age)
        
        # 각 대화의 랜덤 길이를 5분에서 10분 사이로 지정합니다.
        conversation_length_minutes = random.randint(5, 10)

        all_conversations_data = []

        # 요청된 '갯수'만큼 대화문을 생성합니다.
        for i in range(num_conversations):
            # 'Step' (일) 간격으로 대화 날짜를 계산합니다.
            current_date = start_date + timedelta(days=i * step_days)
            
            # LM Studio에 전달할 프롬프트 생성
            prompt = generate_prompt(
                person_name,
                age_group,
                gender,
                situation,
                conversation_length_minutes,
            )

            headers = {"Content-Type": "application/json"}
            payload = {
                "model": "eeve-korean-instruct-10.8b-v1.0", # 사용할 LM Studio 모델명
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 4000,  # 모델이 생성할 수 있는 최대 토큰 수 (필요에 따라 조절)
                "temperature": 0.7,  # 생성된 텍스트의 다양성을 조절 (0.0은 보수적, 1.0은 창의적)
            }

            # 비동기 HTTP 클라이언트를 사용하여 LM Studio API 호출
            async with httpx.AsyncClient(timeout=300.0) as client: # LM Studio 응답 대기 시간 (5분)
                try:
                    response = await client.post(
                        LM_STUDIO_API_URL, headers=headers, json=payload
                    )
                    response.raise_for_status()  # HTTP 오류 (4xx, 5xx) 발생 시 예외 발생
                except httpx.RequestError as exc:
                    # LM Studio 서버에 연결할 수 없는 경우의 오류 처리
                    raise HTTPException(
                        status_code=500,
                        detail=f"LM Studio API 요청 중 오류 발생: {exc}. LM Studio 서버가 실행 중인지 확인해주세요.",
                    )
                except httpx.HTTPStatusError as exc:
                    # LM Studio API가 오류 응답을 반환한 경우의 오류 처리
                    raise HTTPException(
                        status_code=exc.response.status_code,
                        detail=f"LM Studio API 응답 오류: {exc.response.text}. 모델 응답 형식을 확인하세요.",
                    )

            try:
                response_data = response.json()
                if "choices" not in response_data or not response_data["choices"]:
                    raise ValueError("LM Studio 응답에 'choices'가 없거나 비어 있습니다. 모델이 제대로 응답하지 않았습니다.")
                
                # 모델 응답에서 실제 대화 내용을 추출합니다.
                model_output_text = response_data["choices"][0]["message"]["content"]
                
                # 추출된 JSON 문자열을 Python 리스트/딕셔너리로 파싱합니다.
                try:
                    conversation_content = json.loads(model_output_text)
                    if not isinstance(conversation_content, list):
                        raise ValueError("LM Studio 응답이 유효한 JSON 배열이 아닙니다. 모델이 JSON 형식을 따르지 않았습니다.")
                except json.JSONDecodeError:
                    # 모델이 유효한 JSON을 반환하지 못한 경우 처리
                    print(f"Warning: LM Studio 응답이 유효한 JSON이 아닙니다. 원본 텍스트를 저장합니다: {model_output_text}")
                    conversation_content = [{"speaker": "system", "emotion": "정보", "text": model_output_text, "note": "LM Studio 응답이 JSON 형식이 아니었습니다."}]

            except (json.JSONDecodeError, ValueError) as e:
                # 응답 파싱 중 발생한 오류 처리
                raise HTTPException(
                    status_code=500,
                    detail=f"LM Studio 응답 파싱 중 오류 발생: {e}. 응답 내용: {response.text}",
                )

            # 생성된 대화 정보와 요청 파라미터를 함께 저장합니다.
            conversation_entry = {
                "request_parameters": {
                    "person_name": person_name,
                    "age": age,
                    "gender": gender,
                    "situation": situation,
                    "start_date": start_date.isoformat(),
                    "step_days": step_days,
                    "num_conversations": num_conversations
                },
                "generated_at": datetime.now().isoformat(), # 대화가 추출된 시각
                "conversation_date": current_date.isoformat(), # 해당 대화의 기준 날짜
                "conversation_content": conversation_content,
            }
            all_conversations_data.append(conversation_entry)

        # 고유한 파일명 생성 및 JSON 파일로 저장
        filename = f"conversation_{uuid.uuid4()}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_conversations_data, f, ensure_ascii=False, indent=4)

        # JSON 파일을 HTTP 응답으로 반환하여 다운로드되도록 설정
        return Response(
            content=json.dumps(all_conversations_data, ensure_ascii=False, indent=4),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        # Pydantic 모델이 아닌 곳에서 발생한 유효성 검사 오류 (예: age 검사)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # 그 외 예측하지 못한 오류 처리
        raise HTTPException(status_code=500, detail=str(e))

# --- API 엔드포인트 정의 ---

@app.post("/generate_conversation/")
async def generate_conversation_post(request: ConversationRequest):
    """
    **POST 요청**: JSON 요청 본문을 통해 파라미터를 받아 대화문을 생성하고 JSON 파일을 다운로드합니다.
    """
    # Pydantic 모델에서 추출한 데이터를 공통 처리 함수로 전달합니다.
    return await process_conversation_request(
        person_name=request.person_name,
        age=request.age,
        gender=request.gender,
        situation=request.situation,
        start_date=request.start_date,
        step_days=request.step_days,
        num_conversations=request.num_conversations
    )

@app.get("/generate_conversation_get/")
async def generate_conversation_get(
    person_name: str = Query(..., description="대화의 주인공 이름 (텍스트)"),
    age: int = Query(..., ge=13, description="나이 (숫자, 13세 이상)"),
    gender: Literal["male", "female"] = Query(..., description="성별 (male 또는 female)"),
    situation: str = Query(..., description="원하는 컨셉의 대화 상황 (텍스트)"),
    # start_date는 ISO 8601 형식 (예: 2024-06-01T00:00:00 또는 2024-06-01)으로 전달 가능
    start_date: datetime = Query(datetime(2024, 6, 1), description="대화 시작 기준일 (YYYY-MM-DD)"),
    step_days: int = Query(..., ge=1, description="대화 간격 (일, 숫자)"),
    num_conversations: int = Query(..., ge=1, description="생성할 대화문의 총 개수 (숫자)")
):
    """
    **GET 요청**: URL 쿼리 파라미터를 통해 파라미터를 받아 대화문을 생성하고 JSON 파일을 다운로드합니다.
    """
    # 쿼리 파라미터로 받은 데이터를 공통 처리 함수로 전달합니다.
    return await process_conversation_request(
        person_name=person_name,
        age=age,
        gender=gender,
        situation=situation,
        start_date=start_date,
        step_days=step_days,
        num_conversations=num_conversations
    )

# --- 서버 실행 ---

if __name__ == "__main__":
    import uvicorn
    # Uvicorn을 사용하여 FastAPI 앱을 8080번 포트로 실행합니다.
    # 'host="0.0.0.0"'은 외부에서도 접근 가능하게 합니다.
    uvicorn.run(app, host="0.0.0.0", port=8080)