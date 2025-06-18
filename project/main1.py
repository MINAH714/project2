# from fastapi import FastAPI, BackgroundTasks
# from fastapi.responses import FileResponse
# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import datetime, timedelta
# from pathlib import Path
# import random
# import json
# import uuid
# import requests

# app = FastAPI()

# BASE_DIR = Path(__file__).parent
# OUTPUT_FOLDER = BASE_DIR / "dummy_data"
# OUTPUT_FOLDER.mkdir(exist_ok=True)

# def age_group(age: int) -> str:
#     if 13 <= age <= 19:
#         return "teenager"
#     elif 20 <= age <= 39:
#         return "adult_young"
#     elif 40 <= age <= 65:
#         return "adult_middle"
#     elif age > 65:
#         return "senior"
#     else:
#         return "not_target"

# class DummyRequest(BaseModel):
#     name: str = Field(..., example="Alice", description="이름")
#     age: int = Field(..., example=17, description="나이 (13세 이상만 가능)")
#     gender: str = Field(..., example="female", description="성별 (male/female)")
#     situation: str = Field(..., example="감정 변화", description="상황 (자유 입력)")
#     timestamp: Optional[str] = Field(None, example="2025-06-01", description="시작 날짜 (YYYY-MM-DD, 미입력시 2025-06-01)")
#     step: int = Field(..., example=3, description="Step(일) : 대화문 간 날짜 간격")
#     count: int = Field(..., example=4, description="갯수 : 생성할 대화문 세트 개수")

# def get_dialogue_from_llm(name, age, gender, situation, minutes, dialogue_count, date):
#     prompt = (
#         f"이름: {name}, 나이: {age}, 성별: {gender}, 상황: {situation}, 날짜: {date}\n"
#         f"{minutes:.1f}분 동안의 감정 공감형 대화문 {dialogue_count}개를 생성해줘. "
#         "각 대화문은 1~2문장으로, 자연스럽고 현실적으로 만들어줘. "
#         "각 대화문은 json 배열로 반환해줘. 예시: [\"대화1\", \"대화2\", ...]"
#     )
#     response = requests.post(
#         "http://localhost:1234/v1/completions",  # LM Studio API 엔드포인트 예시
#         json={
#             "model": "eeve-korean-instruct-10.8b-v1.0",
#             "prompt": prompt,
#             "stream": False
#         }
#     )
#     result = response.json()
#     try:
#         dialogues = json.loads(result["choices"][0]["text"])
#         if isinstance(dialogues, list):
#             return dialogues
#     except Exception:
#         return result["choices"][0]["text"].split("\n")
#     return []

# @app.post("/generate-dummy/")
# def generate_dummy(data: DummyRequest, background_tasks: BackgroundTasks):
#     group = age_group(data.age)
#     if group == "not_target":
#         return {"error": "나이가 대상 연령대가 아닙니다. (13세 이상만 가능)"}
#     situation = data.situation  # 사용자가 입력한 상황을 그대로 사용
#     start_date = datetime.strptime(data.timestamp, "%Y-%m-%d") if data.timestamp else datetime(2025, 6, 1)
#     result = []
#     for i in range(data.count):
#         current_date = start_date + timedelta(days=i * data.step)
#         minutes = random.uniform(5, 10)
#         dialogue_count = random.randint(int(minutes * 10), int(minutes * 11))
#         dialogues = get_dialogue_from_llm(
#             data.name, data.age, data.gender, situation, minutes, dialogue_count, current_date.strftime("%Y-%m-%d")
#         )
#         dialogue_objs = [
#             {
#                 "speaker": data.name,
#                 "text": text,
#                 "timestamp": current_date.strftime("%Y-%m-%d")
#             }
#             for text in dialogues
#         ]
#         result.append({
#             "date": current_date.strftime("%Y-%m-%d"),
#             "name": data.name,
#             "age": data.age,
#             "age_group": group,
#             "gender": data.gender,
#             "situation": situation,
#             "step": data.step,
#             "dialogues": dialogue_objs
#         })
#     filename = f"dummy_{data.name}_{uuid.uuid4().hex}.json"
#     filepath = OUTPUT_FOLDER / filename
#     with open(filepath, "w", encoding="utf-8") as f:
#         json.dump(result, f, ensure_ascii=False, indent=2)
#     return {"filename": filename, "path": str(filepath)}

# @app.get("/download/{filename}")
# def download_file(filename: str):
#     filepath = OUTPUT_FOLDER / filename
#     return FileResponse(filepath, media_type="application/json", filename=filename)

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import random
import json
import uuid
import requests
import re

app = FastAPI()

BASE_DIR = Path(__file__).parent
OUTPUT_FOLDER = BASE_DIR / "dummy_data"
OUTPUT_FOLDER.mkdir(exist_ok=True)

def age_group(age: int) -> str:
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

class DummyRequest(BaseModel):
    name: str = Field(..., example="Alice", description="이름")
    age: int = Field(..., example=17, description="나이 (13세 이상만 가능)")
    gender: str = Field(..., example="female", description="성별 (male/female)")
    situation: str = Field(..., example="감정 변화", description="상황 (자유 입력)")
    timestamp: Optional[str] = Field(None, example="2025-06-01", description="시작 날짜 (YYYY-MM-DD, 미입력시 2025-06-01)")
    step: int = Field(..., example=3, description="Step(일) : 대화문 간 날짜 간격")
    count: int = Field(..., example=4, description="갯수 : 생성할 대화문 세트 개수")

def extract_dialogues(response_text):
    # 코드블록, 줄바꿈, 공백 제거
    response_text = response_text.strip()
    response_text = re.sub(r"^``````$", "", response_text, flags=re.MULTILINE)
    # JSON 배열 추출
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            # 빈 문자열 없이 반환
            return [d for d in data if d.strip()]
    except Exception:
        # 정규식으로 배열 내부만 추출
        matches = re.findall(r'$$"(.*?)"$$', response_text, re.DOTALL)
        if matches:
            return [m.replace('\n', '').strip() for m in matches if m.strip()]
    # 마지막 방어: 줄 단위 추출
    lines = [line.strip() for line in response_text.split("\n") if line.strip()]
    return [line for line in lines if line]

def get_dialogue_from_llm(name, age, gender, situation, minutes, dialogue_count, date):
    prompt = (
        f"이름: {name}, 나이: {age}, 성별: {gender}, 상황: {situation}, 날짜: {date}\n"
        f"{minutes:.1f}분 동안의 감정 공감형 대화문 {dialogue_count}개를 생성해줘. "
        "각 대화문은 1~2문장으로, 자연스럽고 현실적으로 만들어줘. "
        "각 대화문은 아래와 같은 JSON 배열로만 반환해줘. 예시: [\"오늘 점심시간에 친구들이 제가 좋아하는 음식으로 케이크 사서 먹으려고 했는데, 나도 못 참고 엄마 전화 받아서 가게 들어갈 때까지 지연되다가 그때 이미 다 파워없었어... 진짜 속상하다.\"]"
    )
    response = requests.post(
        "http://localhost:1234/v1/completions",
        json={
            "model": "eeve-korean-instruct-10.8b-v1.0",
            "prompt": prompt,
            "stream": False
        }
    )
    result = response.json()
    text = result.get("choices", [{}]).get("text", "")
    return extract_dialogues(text)

@app.post("/generate-dummy/")
def generate_dummy(data: DummyRequest, background_tasks: BackgroundTasks):
    group = age_group(data.age)
    if group == "not_target":
        return {"error": "나이가 대상 연령대가 아닙니다. (13세 이상만 가능)"}
    situation = data.situation
    start_date = datetime.strptime(data.timestamp, "%Y-%m-%d") if data.timestamp else datetime(2025, 6, 1)
    result = []
    for i in range(data.count):
        current_date = start_date + timedelta(days=i * data.step)
        minutes = random.uniform(5, 10)
        dialogue_count = random.randint(int(minutes * 10), int(minutes * 11))
        dialogues = get_dialogue_from_llm(
            data.name, data.age, data.gender, situation, minutes, dialogue_count, current_date.strftime("%Y-%m-%d")
        )
        dialogue_objs = [
            {
                "speaker": data.name,
                "text": text,
                "timestamp": current_date.strftime("%Y-%m-%d")
            }
            for text in dialogues
        ]
        result.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "name": data.name,
            "age": data.age,
            "age_group": group,
            "gender": data.gender,
            "situation": situation,
            "step": data.step,
            "dialogues": dialogue_objs
        })
    filename = f"dummy_{data.name}_{uuid.uuid4().hex}.json"
    filepath = OUTPUT_FOLDER / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return {"filename": filename, "path": str(filepath)}

@app.get("/download/{filename}")
def download_file(filename: str):
    filepath = OUTPUT_FOLDER / filename
    return FileResponse(filepath, media_type="application/json", filename=filename)
