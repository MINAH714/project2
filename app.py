from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
import re
from pathlib import Path

# 데이터 파일 경로
DATA_FILE = Path(__file__).parent / "emotion_chatbot_data.json"

# 마크다운 코드 블록 제거 함수
def clean_json_block(raw: str) -> Optional[dict]:
    # `````` 또는 `````` 제거
    if not isinstance(raw, str):
        return None
    match = re.search(r"``````", raw)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    # 혹시 코드블록이 없고 순수 JSON일 경우
    try:
        return json.loads(raw)
    except Exception:
        return None

# 데이터 로드 및 정제
def load_dialogues():
    with open(DATA_FILE, encoding="utf-8") as f:
        raw_data = json.load(f)
    result = []
    for person, emotions in raw_data.items():
        for emotion, items in emotions.items():
            for item in items:
                if "raw" in item:
                    parsed = clean_json_block(item["raw"])
                    if parsed:
                        parsed["person"] = person
                        parsed["emotion"] = emotion
                        result.append(parsed)
                # 혹시 정상 JSON이 바로 들어있는 경우
                elif all(k in item for k in ("age_group", "gender", "emotion", "role", "content")):
                    item["person"] = person
                    item["emotion"] = emotion
                    result.append(item)
    return result

# 데이터 메모리에 로드
dialogues = load_dialogues()

app = FastAPI(title="Emotion Chatbot Data API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Emotion Chatbot Data API is running."}

@app.get("/api/get_dialogues")
def get_dialogues(
    age_group: Optional[str] = Query(None, description="연령층 (예: 청소년, 성인, 노년층)"),
    gender: Optional[str] = Query(None, description="성별 (예: 여성, 남성)"),
    emotion: Optional[str] = Query(None, description="감정 (예: 기쁨, 분노, 슬픔 등)")
):
    filtered = [
        d for d in dialogues
        if (not age_group or d.get("age_group") == age_group)
        and (not gender or d.get("gender") == gender)
        and (not emotion or d.get("emotion") == emotion)
    ]
    if not filtered:
        raise HTTPException(status_code=404, detail="조건에 맞는 대화 데이터가 없습니다.")
    return filtered

# 개발용 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
