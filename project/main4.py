from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import requests
import json
import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Union

app = FastAPI(
    title="AI 공감형 대화문 생성기 API (감정 포함)",
    description="LM Studio를 활용하여 사용자 설정에 맞는 감정 변화를 포함하는 공감형 대화문을 생성합니다."
)

# 요청 바디 정의 (기존과 동일)
class DialogueRequest(BaseModel):
    name: str = Field(..., example="Alice", description="대화할 사람의 이름")
    age: int = Field(..., ge=13, le=100, example=17, description="대화할 사람의 나이 (13세 이상)")
    gender: str = Field(..., example="female", description="대화할 사람의 성별 (male/female)")
    situation: str = Field(..., example="학교 생활", description="대화가 이루어질 상황")
    start_date: str = Field(..., example="2025-06-01", description="대화 리포트의 기준 시작 날짜 (YYYY-MM-DD 형식)")
    step_days: int = Field(..., ge=1, example=3, description="각 회차(날짜) 간의 간격 (일)")
    num_dialogues_per_step: int = Field(..., ge=1, example=4, description="생성할 회차(날짜)의 갯수")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "Alice",
                    "age": 17,
                    "gender": "female",
                    "situation": "학교 생활",
                    "start_date": "2025-06-01",
                    "step_days": 3,
                    "num_dialogues_per_step": 4
                }
            ]
        }

@app.post("/generate_dialogues", response_model=Dict[str, Union[str, List[Dict[str, Union[str, List[Dict[str, Union[str, List[str]]]]]]]]])
async def generate_dialogues(request: DialogueRequest):
    """
    사용자 정보와 상황에 기반한 공감형 대화문을 생성하고, 각 대화에 느껴지는 감정을 포함하여 반환합니다.
    챗봇과 사용자의 대화가 번갈아 가며 생성되며, 대화 흐름에 따라 감정이 변화하는 것을 반영하려고 합니다.
    가능한 감정은 '기쁨', '분노', '슬픔', '두려움', '놀람', '혐오'의 6가지입니다.
    """
    emotions = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]
    try:
        dialogue_results = []
        
        start_dt_only_date = date.fromisoformat(request.start_date)

        # Step과 갯수를 고려한 대화 생성
        for i in range(request.num_dialogues_per_step):
            current_date_for_dialogues = start_dt_only_date + timedelta(days=request.step_days * i)
            current_date_str = current_date_for_dialogues.strftime("%Y-%m-%d")

            minutes = random.uniform(5, 10)
            # 챗봇-사용자 '쌍' 대화 턴 수. 각 턴은 2개의 발화로 구성.
            dialogue_turns_count = random.randint(int(minutes * 5), int(minutes * 5.5)) 

            dialogue_start_time = datetime.combine(current_date_for_dialogues, datetime.min.time()) + timedelta(hours=random.randint(8, 10), minutes=random.randint(0, 59))

            # LM Studio API 프롬프트 생성 - JSON 형식 예시를 더욱 명확하고 요청하신 구조에 가깝게 제시
            prompt = (
                f"당신은 사용자의 감정을 공감하고 지원하는 챗봇입니다. "
                f"사용자는 '{request.name}'(나이: {request.age}세, 성별: {'남성' if request.gender == 'male' else '여성'})이며, 현재 '{request.situation}' 상황에 있습니다. "
                f"오늘 날짜는 {current_date_str} 입니다.\n"
                f"{minutes:.1f}분 동안 진행될 챗봇과 사용자의 공감형 대화문 {dialogue_turns_count}쌍(턴)을 생성해줘. "
                "각 대화는 1~2문장으로 자연스럽고 현실적으로 만들어줘. "
                "대화는 사용자의 감정을 이해하고 긍정적인 방향으로 이끌어가는 데 초점을 맞춰야 해. "
                f"대화가 진행됨에 따라 사용자와 챗봇의 감정이 자연스럽게 변화하는 모습을 보여줘. "
                f"생성된 대화에 나타나는 감정은 '{', '.join(emotions)}' 중 하나 또는 여러 개가 될 수 있어. "
                "응답은 반드시 JSON 배열 형태로만 제공해야 해. 배열의 각 요소는 하나의 날짜에 대한 대화 기록 객체여야 해. "
                "각 날짜 기록 객체는 '날짜' 필드와 '대화목록' 배열을 포함해야 해. "
                "각 대화목록 요소는 '시간', '화자', '텍스트', '감정' 필드를 포함해야 해. '감정'은 해당 대화 텍스트에서 느껴지는 주요 감정들을 담은 배열이야.\n"
                "다른 설명이나 추가적인 문장 없이 JSON 배열만 출력해야 해. 다음 예시 형식을 정확히 따라야 해.\n"
                f"예시:\n"
                f"[\n"
                f"  {{\n"
                f"    \"날짜\": \"{current_date_str}\",\n"
                f"    \"대화목록\": [\n"
                f"      {{\n"
                f"        \"시간\": \"{dialogue_start_time.strftime('%H:%M')}\",\n"
                f"        \"화자\": \"사용자\",\n"
                f"        \"텍스트\": \"오늘 학교에서 발표를 망쳐서 너무 슬프고 화가 나요.\",\n"
                f"        \"감정\": [\"슬픔\", \"분노\"]\n"
                f"      }},\n"
                f"      {{\n"
                f"        \"시간\": \"{(dialogue_start_time + timedelta(minutes=random.randint(1,2))).strftime('%H:%M')}\",\n"
                f"        \"화자\": \"챗봇\",\n"
                f"        \"텍스트\": \"정말 속상하고 힘들었겠어요. 어떤 부분이 가장 힘들었나요? 제가 공감해 드릴게요.\",\n"
                f"        \"감정\": [\"공감\", \"위로\"]\n" # 챗봇의 감정도 표현 가능하도록 (여기서는 예시이므로 '공감' 추가)
                f"      }}\n"
                f"    ]\n"
                f"  }}\n"
                f"]"
            )

            # LM Studio API 호출 (이전 코드와 동일)
            api_url = "http://localhost:1234/v1/completions" # LM Studio 서버 URL 확인
            headers = {"Content-Type": "application/json"}
            body = {
                "model": "eeve-korean-instruct-10.8b-v1.0", # 사용 중인 모델 이름 확인
                "prompt": prompt,
                "max_tokens": 4096,
                "temperature": 0.7,
                "stop": ["```", "```json"] # JSON 응답 외 다른 출력 방지
            }
            
            lm_res = requests.post(api_url, headers=headers, json=body, timeout=300) 
            lm_res.raise_for_status() 

            lm_result = lm_res.json()
            
            extracted_text = ""
            if 'choices' in lm_result and len(lm_result['choices']) > 0 and 'text' in lm_result['choices'][0]:
                extracted_text = lm_result['choices'][0]['text'].strip()
                # 마크다운 코드 블록 제거 로직 (더욱 엄격하게 JSON 배열로 시작하는지 확인)
                if extracted_text.startswith("```json"):
                    extracted_text = extracted_text[len("```json"):].strip()
                if extracted_text.endswith("```"):
                    extracted_text = extracted_text[:-len("```")].strip()
            
            # LM Studio 응답 파싱 로직 수정: 이제 전체 JSON 배열을 기대
            parsed_lm_data = []
            if extracted_text:
                try:
                    parsed_lm_data = json.loads(extracted_text)
                    if not isinstance(parsed_lm_data, list) or \
                       not all(isinstance(item, dict) and "날짜" in item and "대화목록" in item for item in parsed_lm_data):
                        raise ValueError("LM Studio 응답이 예상된 JSON 배열 형식이 아닙니다.")
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                    print(f"원본 텍스트: {extracted_text}")
                    raise HTTPException(status_code=500, detail={
                        "message": f"LM Studio 응답 JSON 파싱 오류: {e}",
                        "error_details": extracted_text
                    })
                except ValueError as e:
                    print(f"데이터 형식 오류: {e}")
                    print(f"원본 텍스트: {extracted_text}")
                    raise HTTPException(status_code=500, detail={
                        "message": f"LM Studio 응답 데이터 형식 오류: {e}",
                        "error_details": extracted_text
                    })
            else:
                raise HTTPException(status_code=500, detail={"message": "LM Studio에서 대화 내용이 응답되지 않았습니다.", "error_details": "No text received from LM Studio."})

            # LM Studio에서 받은 데이터를 바탕으로 결과 구성
            # LM Studio가 이미 요청한 형식대로 날짜별 대화목록을 생성해 주었다고 가정
            for daily_entry in parsed_lm_data:
                date_from_lm = daily_entry.get("날짜", current_date_str)
                daily_dialogues_list = []
                
                # 각 대화에 실제 시간 정보를 추가 (LM Studio가 임의 시간 생성 가능하도록 프롬프트에 예시를 줬지만, 여기서도 다시 처리)
                dialogue_time_pointer = datetime.combine(current_date_for_dialogues, dialogue_start_time.time())
                
                if daily_entry.get("대화목록"):
                    # 총 대화 시간에 해당하는 초
                    total_seconds_for_dialogues = minutes * 60 
                    # 실제 생성된 대화 발화 수 (각 턴이 사용자+챗봇이므로 총 발화 수는 턴 수의 2배가 될 수 있지만,
                    # LM Studio가 대화목록에 직접 리스트로 넣어주므로 그 길이를 사용)
                    actual_dialogues_generated = len(daily_entry["대화목록"])
                    avg_interval_seconds_per_dialogue = total_seconds_for_dialogues / actual_dialogues_generated if actual_dialogues_generated > 0 else 0

                    for k, dialogue_item_from_lm in enumerate(daily_entry["대화목록"]):
                        if avg_interval_seconds_per_dialogue > 0:
                            interval = random.uniform(avg_interval_seconds_per_dialogue * 0.5, avg_interval_seconds_per_dialogue * 1.5)
                            dialogue_time_pointer += timedelta(seconds=interval)

                        if dialogue_time_pointer.date() > current_date_for_dialogues:
                            dialogue_time_pointer = datetime.combine(current_date_for_dialogues, datetime.max.time())

                        daily_dialogues_list.append({
                            "time": dialogue_time_pointer.strftime("%H:%M:%S"), # 실제 시간으로 재설정
                            "speaker": dialogue_item_from_lm.get("화자", "알 수 없음"),
                            "dialogue_text": dialogue_item_from_lm.get("텍스트", "대화 내용 없음"),
                            "emotions": dialogue_item_from_lm.get("감정", [])
                        })
                
                # FastAPI 응답 형식에 맞게 변환
                dialogue_results.append({
                    "name": request.name,
                    "age": request.age,
                    "gender": request.gender,
                    "situation": request.situation,
                    "date": date_from_lm, # LM Studio가 준 날짜 또는 기본값
                    "daily_dialogues": daily_dialogues_list
                })

        return {"status": "success", "message": "감정 정보가 포함된 대화문이 성공적으로 생성되었습니다.", "data": dialogue_results}

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail={"message": "LM Studio 서버 응답 시간 초과", "error_details": "LM Studio API connection timed out."})
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail={"message": "LM Studio 서버 연결 실패", "error_details": "Could not connect to LM Studio API."})
    except requests.exceptions.RequestException as e:
        error_detail = ""
        if 'lm_res' in locals():
            try:
                error_detail = lm_res.json()
            except json.JSONDecodeError:
                error_detail = lm_res.text
        raise HTTPException(status_code=500, detail={"message": f"LM Studio API 오류: {e}", "error_details": error_detail})
    except json.JSONDecodeError as e: # LM Studio 응답 자체의 JSON 파싱 오류는 위에서 처리되므로 여기는 남은 경우
        raise HTTPException(status_code=500, detail={"message": f"LM Studio 응답을 최종 파싱하는 도중 오류: {e}", "error_details": extracted_text if 'extracted_text' in locals() else "응답 텍스트 없음"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"서버 오류: {e}", "error_details": str(e)})