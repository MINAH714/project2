# main.py 또는 main7.py 파일에 다음 코드 추가 (기존 코드 아래에 추가)

from fastapi.responses import StreamingResponse
import asyncio # 비동기 처리를 위해 asyncio 임포트

# --- 스트리밍 응답을 위한 새로운 엔드포인트 ---

@app.get("/stream_conversation_get/")
async def stream_conversation_get(
    person_name: str = Query(..., description="대화의 주인공 이름 (텍스트)"),
    age: int = Query(..., ge=13, description="나이 (숫자, 13세 이상)"),
    gender: Literal["male", "female"] = Query(..., description="성별 (male 또는 female)"),
    situation: str = Query(..., description="원하는 컨셉의 대화 상황 (텍스트)"),
    start_date: datetime = Query(datetime(2024, 6, 1), description="대화 시작 기준일 (YYYY-MM-DD)"),
    step_days: int = Query(..., ge=1, description="대화 간격 (일, 숫자)"),
    num_conversations: int = Query(..., ge=1, description="생성할 대화문의 총 개수 (숫수)")
):
    """
    (GET - Streaming) 쿼리 파라미터를 통해 대화 생성 파라미터를 받아
    대화문을 LM Studio로부터 스트리밍 방식으로 받아 실시간으로 전송합니다.
    """
    try:
        if 1 <= age <= 12:
            raise ValueError("1-12세는 너무 어려서 대상이 아닙니다. 13세 이상만 가능합니다.")

        age_group = get_age_group(age)
        conversation_length_minutes = random.randint(5, 10)

        async def generate_and_stream_conversations():
            all_generated_data = [] # 전체 데이터를 저장할 리스트

            for i in range(num_conversations):
                current_date = start_date + timedelta(days=i * step_days)
                prompt = generate_prompt(
                    person_name, age_group, gender, situation, conversation_length_minutes
                )

                headers = {"Content-Type": "application/json"}
                payload = {
                    "model": "eeve-korean-instruct-10.8b-v1.0",
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "stream": True # LM Studio에 스트리밍 요청
                }

                yield f"**{i+1}/{num_conversations}번째 대화 생성 중... (날짜: {current_date.strftime('%Y-%m-%d')})**\n\n"
                
                full_response_content = "" # 스트리밍 응답을 모을 변수

                async with httpx.AsyncClient(timeout=300.0) as client:
                    try:
                        async with client.stream("POST", LM_STUDIO_API_URL, headers=headers, json=payload, timeout=None) as r:
                            r.raise_for_status()
                            async for chunk in r.aiter_bytes():
                                try:
                                    chunk_str = chunk.decode("utf-8")
                                    # LM Studio는 각 데이터 청크를 "data: {json}\n\n" 형식으로 보냅니다.
                                    # "data: " 접두사를 제거하고 JSON 파싱을 시도합니다.
                                    for line in chunk_str.splitlines():
                                        if line.startswith("data: "):
                                            json_data = line[len("data: "):]
                                            if json_data.strip() == "[DONE]":
                                                continue # 스트림 종료 마커
                                            try:
                                                data = json.loads(json_data)
                                                if "choices" in data and data["choices"]:
                                                    delta = data["choices"][0]["delta"]
                                                    if "content" in delta:
                                                        content = delta["content"]
                                                        full_response_content += content
                                                        yield content # Streamlit으로 내용 바로 전송
                                            except json.JSONDecodeError:
                                                # 유효하지 않은 JSON 데이터 처리 (로그만 남기고 스킵)
                                                print(f"Invalid JSON chunk: {json_data}")
                                                continue
                                except UnicodeDecodeError:
                                    print(f"UnicodeDecodeError on chunk: {chunk}")
                                    continue
                    except httpx.RequestError as exc:
                        yield f"LM Studio API 요청 중 오류 발생: {exc}. LM Studio 서버가 실행 중인지 확인해주세요."
                        return # 오류 발생 시 스트림 종료
                    except httpx.HTTPStatusError as exc:
                        yield f"LM Studio API 응답 오류: {exc.response.status_code} - {exc.response.text}"
                        return # 오류 발생 시 스트림 종료
                
                # 각 대화 생성이 완료되면 전체 대화 내용을 파싱하고 저장
                try:
                    conversation_content = json.loads(full_response_content)
                    if not isinstance(conversation_content, list):
                        raise ValueError("LM Studio 응답이 유효한 JSON 배열이 아닙니다.")
                except json.JSONDecodeError:
                    print(f"Warning: LM Studio 응답이 유효한 JSON이 아닙니다. 원본 텍스트를 저장합니다: {full_response_content}")
                    conversation_content = [{"speaker": "system", "emotion": "정보", "text": full_response_content, "note": "LM Studio 응답이 JSON 형식이 아니었습니다."}]
                except ValueError as e:
                    print(f"Error processing model output: {e} - {full_response_content}")
                    conversation_content = [{"speaker": "system", "emotion": "에러", "text": f"모델 출력 처리 오류: {e}", "note": "JSON 파싱 실패"}]
                
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
                    "generated_at": datetime.now().isoformat(),
                    "conversation_date": current_date.isoformat(),
                    "conversation_content": conversation_content,
                }
                all_generated_data.append(conversation_entry)
                yield "\n\n---\n\n" # 각 대화 사이 구분자
            
            # 모든 대화 생성이 완료되면 전체 데이터를 Session State에 저장
            # Streamlit 앱에서 이 데이터를 다운로드 버튼에 사용할 것임
            # 이 부분은 Streamlit 앱 내에서 직접 처리하는 것이 더 적절합니다.
            # yield를 통해서는 큰 데이터를 한 번에 전달하기 어렵습니다.
            # 따라서 최종 JSON 저장 및 다운로드는 Streamlit 앱에서 별도로 호출하는 방식으로 변경합니다.

            # 최종적으로, 모든 데이터가 모아진 것을 Streamlit이 다운로드 할 수 있도록
            # JSON 데이터를 클라이언트에 다시 제공하는 엔드포인트는 기존의 /generate_conversation_get 이 담당.
            # 스트리밍 엔드포인트는 오직 실시간 출력을 위함.
            
            #yield f"생성 완료! 모든 데이터는 FastAPI 서버에 저장되었으며, 다운로드 버튼을 통해 전체 데이터를 받을 수 있습니다."

        return StreamingResponse(generate_and_stream_conversations(), media_type="text/event-stream")

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))