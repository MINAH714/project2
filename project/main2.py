from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import random
from datetime import date, timedelta
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
        
        start_dt = date.fromisoformat(request.start_date)

        # Step과 갯수를 고려한 대화 생성
        for i in range(request.num_dialogues_per_step):
            current_date = start_dt + timedelta(days=request.step_days * i)
            current_date_str = current_date.strftime("%Y-%m-%d")

            # 대화문의 양 랜덤 지정 (5분-10분)
            minutes = random.uniform(5, 10)
            # 1분당 대화문 10-11개
            dialogue_count = random.randint(int(minutes * 10), int(minutes * 11))

            # LM Studio API 프롬프트 생성
            prompt = (
                f"이름: {request.name}, 나이: {request.age}, 성별: {request.gender}, "
                f"상황: {request.situation}, 날짜: {current_date_str}\n"
                f"{minutes:.1f}분 동안의 감정 공감형 대화문 {dialogue_count}개를 생성해줘. "
                "각 대화문은 1~2문장으로, 자연스럽고 현실적으로 만들어줘. "
                "반드시 JSON 배열 형태로만 응답해줘. 예시: [\"대화1\", \"대화2\", \"대화3\", ...]"
                "다른 설명이나 추가적인 문장 없이 JSON 배열만 출력해야 해."
            )

            # LM Studio API 호출 (포트/모델명 환경에 맞게 수정)
            api_url = "http://localhost:1234/v1/completions" # LM Studio API 주소
            headers = {"Content-Type": "application/json"}
            body = {
                "model": "eeve-korean-instruct-10.8b-v1.0", # 사용하려는 모델명
                "prompt": prompt,
                "max_tokens": 2048, # 응답받을 최대 토큰 수
                "temperature": 0.7, # 창의성 조절 (0.0은 가장 예측 가능, 1.0은 더 창의적)
                "stop": ["```", "```json"] # 응답이 JSON 코드 블록으로 끝나는 경우를 대비한 stop 시퀀스 추가
            }
            
            lm_res = requests.post(api_url, headers=headers, json=body, timeout=180) # LM Studio 요청 타임아웃 3분
            lm_res.raise_for_status() # HTTP 오류 발생 시 예외 발생

            lm_result = lm_res.json()
            
            extracted_text = ""
            if 'choices' in lm_result and len(lm_result['choices']) > 0 and 'text' in lm_result['choices'][0]:
                extracted_text = lm_result['choices'][0]['text'].strip()
                # Markdown 코드 블록이 있다면 제거
                if extracted_text.startswith("```json"):
                    extracted_text = extracted_text[len("```json"):].strip()
                if extracted_text.endswith("```"):
                    extracted_text = extracted_text[:-len("```")].strip()
            
            dialogues = []
            if extracted_text:
                try:
                    dialogues = json.loads(extracted_text)
                    if not isinstance(dialogues, list):
                        raise ValueError("LM Studio 응답이 JSON 배열 형식이 아닙니다.")
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                    print(f"원본 텍스트: {extracted_text}")
                    # LM Studio가 유효한 JSON을 반환하지 않았을 경우, 일단 텍스트를 그대로 저장
                    dialogues = [extracted_text] if extracted_text else ["대화 생성 실패"]
                except ValueError as e:
                    print(f"데이터 형식 오류: {e}")
                    print(f"원본 텍스트: {extracted_text}")
                    dialogues = [extracted_text] if extracted_text else ["대화 생성 실패"]
            else:
                dialogues = ["대화 내용 없음"]

            # 생성된 대화문 중 하나를 랜덤으로 선택 (혹은 모두 저장해도 됨)
            # 여기서는 요청에 따라 '갯수'가 전체 대화문의 갯수가 아니라 '회차'의 갯수로 해석되었습니다.
            # 만약 한 회차에 여러 대화문을 생성하고 싶다면, LM Studio로부터 받은 dialogues 리스트 전체를 저장할 수 있습니다.
            selected_dialogue = random.choice(dialogues) if dialogues else "대화 생성 실패"
            
            dialogue_results.append({
                "name": request.name,
                "age": request.age,
                "gender": request.gender,
                "situation": request.situation,
                "date": current_date_str,
                "dialogue": selected_dialogue # 여기서는 한 회차에 하나의 랜덤 대화문만 저장
                # 만약 모든 대화를 저장하고 싶다면 "dialogues": dialogues 로 변경
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