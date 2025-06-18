from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import random
from datetime import date, datetime, timedelta # datetime 임포트 추가
from typing import List, Dict, Union

app = FastAPI()

# 요청 바디 정의
class DialogueRequest(BaseModel):
    name: str
    age: int
    gender: str
    situation: str
    start_date: str # "YYYY-MM-DD" 형식의 문자열
    step_days: int
    num_dialogues_per_step: int

@app.post("/generate_dialogues")
async def generate_dialogues(request: DialogueRequest):
    try:
        dialogue_results = []
        
        start_dt_only_date = date.fromisoformat(request.start_date)

        # Step과 갯수를 고려한 대화 생성
        for i in range(request.num_dialogues_per_step):
            current_date_for_dialogues = start_dt_only_date + timedelta(days=request.step_days * i)
            current_date_str = current_date_for_dialogues.strftime("%Y-%m-%d")

            # 대화문의 양 랜덤 지정 (5분-10분)
            minutes = random.uniform(5, 10)
            # 1분당 대화문 10-11개
            dialogue_count = random.randint(int(minutes * 10), int(minutes * 11))

            # 해당 날짜의 대화 시작 시간을 임의로 설정 (예: 9시 0분 0초)
            # 실제 사용 시, 이 시작 시간을 더 유연하게 설정할 수 있습니다.
            dialogue_start_time = datetime.combine(current_date_for_dialogues, datetime.min.time()) + timedelta(hours=random.randint(8, 10), minutes=random.randint(0, 59)) # 8시~10시 사이 랜덤 시작

            # LM Studio API 프롬프트 생성 (여기서는 시간 정보를 포함하지 않고 대화문만 요청)
            # LM Studio가 정확한 시간별 대화를 생성하기 어렵기 때문.
            prompt = (
                f"이름: {request.name}, 나이: {request.age}, 성별: {request.gender}, "
                f"상황: {request.situation}, 날짜: {current_date_str}\n"
                f"{minutes:.1f}분 동안의 감정 공감형 대화문 {dialogue_count}개를 생성해줘. "
                "각 대화문은 1~2문장으로, 자연스럽고 현실적으로 만들어줘. "
                "반드시 JSON 배열 형태로만 응답해줘. 예시: [\"대화1\", \"대화2\", \"대화3\", ...]"
                "다른 설명이나 추가적인 문장 없이 JSON 배열만 출력해야 해."
            )

            # LM Studio API 호출 (이전 코드와 동일)
            api_url = "http://localhost:1234/v1/completions" 
            headers = {"Content-Type": "application/json"}
            body = {
                "model": "eeve-korean-instruct-10.8b-v1.0",
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.7,
                "stop": ["```", "```json"]
            }
            
            lm_res = requests.post(api_url, headers=headers, json=body, timeout=180) 
            lm_res.raise_for_status() 

            lm_result = lm_res.json()
            
            extracted_text = ""
            if 'choices' in lm_result and len(lm_result['choices']) > 0 and 'text' in lm_result['choices'][0]:
                extracted_text = lm_result['choices'][0]['text'].strip()
                if extracted_text.startswith("```json"):
                    extracted_text = extracted_text[len("```json"):].strip()
                if extracted_text.endswith("```"):
                    extracted_text = extracted_text[:-len("```")].strip()
            
            dialogues_from_lm = []
            if extracted_text:
                try:
                    dialogues_from_lm = json.loads(extracted_text)
                    if not isinstance(dialogues_from_lm, list):
                        raise ValueError("LM Studio 응답이 JSON 배열 형식이 아닙니다.")
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                    print(f"원본 텍스트: {extracted_text}")
                    dialogues_from_lm = [extracted_text] if extracted_text else ["대화 생성 실패"]
                except ValueError as e:
                    print(f"데이터 형식 오류: {e}")
                    print(f"원본 텍스트: {extracted_text}")
                    dialogues_from_lm = [extracted_text] if extracted_text else ["대화 생성 실패"]
            else:
                dialogues_from_lm = ["대화 내용 없음"]

            # LM Studio에서 받은 대화 개수와 실제 필요한 대화 개수 중 작은 값을 사용
            actual_dialogue_count = min(len(dialogues_from_lm), dialogue_count)

            # 각 대화에 시, 분, 초 추가
            dialogues_with_timestamps_for_this_date = []
            if actual_dialogue_count > 0:
                # 총 대화 시간에 해당하는 초
                total_seconds_for_dialogues = minutes * 60 
                # 각 대화의 평균 간격 (초)
                avg_interval_seconds = total_seconds_for_dialogues / actual_dialogue_count

                current_time_pointer = dialogue_start_time

                for k in range(actual_dialogue_count):
                    # 랜덤 간격 추가 (평균 간격의 50% ~ 150%)
                    interval = random.uniform(avg_interval_seconds * 0.5, avg_interval_seconds * 1.5)
                    current_time_pointer += timedelta(seconds=interval)

                    # 대화 시간이 하루를 넘어가면 해당 날짜의 23:59:59로 고정 (또는 다음 날로 넘어갈지 결정)
                    # 여기서는 간단히 하루를 넘어가면 그 날의 끝으로 처리
                    if current_time_pointer.date() > current_date_for_dialogues:
                        current_time_pointer = datetime.combine(current_date_for_dialogues, datetime.max.time())
                        
                    dialogues_with_timestamps_for_this_date.append({
                        "time": current_time_pointer.strftime("%H:%M:%S"),
                        "dialogue_text": dialogues_from_lm[k] if k < len(dialogues_from_lm) else "대화 내용 없음"
                    })
            else:
                 dialogues_with_timestamps_for_this_date.append({
                    "time": dialogue_start_time.strftime("%H:%M:%S"),
                    "dialogue_text": "생성된 대화 없음"
                })

            dialogue_results.append({
                "name": request.name,
                "age": request.age,
                "gender": request.gender,
                "situation": request.situation,
                "date": current_date_str,
                "daily_dialogues": dialogues_with_timestamps_for_this_date # 해당 날짜의 대화 목록
            })

        return {"status": "success", "message": "대화문이 성공적으로 생성되었습니다.", "data": dialogue_results}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail={
            "message": f"LM Studio API 요청 중 오류 발생: {e}",
            "error_details": str(e)
        })
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail={
            "message": f"LM Studio로부터 받은 응답을 파싱할 수 없습니다. 유효한 JSON 형식이 아닙니다: {e}",
            "error_details": lm_res.text if 'lm_res' in locals() else "응답 텍스트 없음"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "message": f"서버 처리 중 예상치 못한 오류 발생: {e}",
            "error_details": str(e)
        })