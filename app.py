import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta

# FastAPI server URL
FASTAPI_URL = "http://localhost:8080" # Ensure this matches your FastAPI server port

# --- Streamlit Session State Initialization ---
if 'full_report_data' not in st.session_state:
    st.session_state.full_report_data = []
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
if 'person_name_input_value' not in st.session_state:
    st.session_state.person_name_input_value = ""

# --- Conversation Report Rendering Function ---
def render_conversations_report(report_data):
    st.subheader("생성된 대화 리포트")
    st.markdown("---")
    if report_data:
        for entry in report_data:
            st.markdown(f"#### 날짜: **{entry.get('timestamp', '날짜 정보 없음')}**")
            st.write(f"**이름:** {entry.get('person_name', '')}, **나이:** {entry.get('age', '')}, **성별:** {entry.get('gender', '')}, **상황:** {entry.get('situation', '')}")
            st.markdown("##### 대화 내용:")

            if entry.get('conversation'):
                for dialogue_item in entry['conversation']:
                    speaker = dialogue_item.get('speaker', '알 수 없음')
                    content = dialogue_item.get('content', '')
                    emotions = dialogue_item.get('emotions', [])
                    emotions_str = f" (감정: {', '.join(emotions)})" if emotions else ""
                    st.write(f"- **{speaker}:** {content}{emotions_str}")
            else:
                st.write("해당 날짜에 생성된 대화가 없습니다.")
            st.markdown("---")
    else:
        st.info("아직 생성된 대화가 없습니다.")

# Streamlit App Title
st.set_page_config(layout="wide")
st.title("AI 공감형 대화문 생성기")
st.markdown("---")
st.subheader("대화문 생성 조건 입력")

# --- Parameter Input Form ---
with st.form("conversation_params_form"):
    current_person_name_input = st.text_input(
        "대화할 사람 이름",
        value=st.session_state.person_name_input_value,
        key="person_name_input_widget_key",
        placeholder="이름을 입력하세요 (예: Alice, Peter, Sue)..."
    )

    age = st.number_input("나이", min_value=13, max_value=150, value=21)
    gender = st.radio("성별", ["male", "female"], horizontal=True)

    # Fetch situation options from FastAPI
    @st.cache_data(ttl=3600) # Cache the result for an hour
    def get_fastapi_situation_options(age_val):
        try:
            response = requests.get(f"{FASTAPI_URL}/get_situation_options/", params={"age": age_val})
            response.raise_for_status()
            return response.json().get("situation_options", [])
        except requests.exceptions.RequestException as e:
            st.error(f"상황 옵션을 불러오는 데 실패했습니다: {e}. FastAPI 서버가 실행 중인지 확인해주세요.")
            return []

    situation_options = get_fastapi_situation_options(age)
    
    if not situation_options:
        st.warning("13세 미만은 대화 생성 대상이 아니거나, 상황 옵션을 불러올 수 없습니다.")
        situation = None
    else:
        situation = st.selectbox("상황", situation_options, key="situation_select")
        if not situation: # Check if situation is empty after selection
            st.error("나이 그룹에 해당하는 상황을 선택해주세요.")


    start_date_input = st.date_input("기준 시작 날짜 (YYYY-MM-DD)", value=date(2025, 6, 1))
    start_date_str = start_date_input.isoformat()

    step_days = st.number_input("Step (일 간격)", min_value=1, value=3)
    num_conversations = st.number_input("생성할 대화문 갯수 (회차)", min_value=1, value=4)

    st.markdown("---")
    
    submitted = st.form_submit_button("AI 대화문 생성", disabled=st.session_state.is_generating)

# --- Conversation Generation Logic ---
if submitted:
    st.session_state.person_name_input_value = current_person_name_input
    person_name_final = st.session_state.person_name_input_value

    if not person_name_final.strip():
        st.error("대화할 사람 이름을 입력해주세요.")
        st.session_state.is_generating = False
    elif situation is None or not situation:
        st.error("상황을 선택하거나 유효한 나이를 입력하여 상황 옵션을 불러와 주세요.")
        st.session_state.is_generating = False
    else:
        st.session_state.is_generating = True
        st.session_state.full_report_data = []
        st.info("AI 대화문을 생성 중입니다. 잠시 기다려 주세요...")

        progress_container = st.empty()
        report_placeholder = st.empty()

        request_payload = {
            "person_name": person_name_final,
            "age": age,
            "gender": gender,
            "situation": situation,
            "start_timestamp": start_date_str,
            "step_days": step_days,
            "num_conversations": num_conversations
        }

        fastapi_stream_endpoint = f"{FASTAPI_URL}/generate-stream/" # Updated endpoint name

        try:
            with requests.post(fastapi_stream_endpoint, json=request_payload, stream=True, timeout=None) as response: # timeout=None for long streams
                response.raise_for_status()

                # Process each line from the streaming response
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        try:
                            # Streamlit requires a single JSON object per line for streaming
                            # FastAPI is set to send one JSON object per 'yield' + newline
                            chunk = json.loads(decoded_line)

                            if chunk.get("status") == "generating":
                                progress_container.info(chunk.get("message"))
                            elif chunk.get("status") == "progress":
                                progress_container.text(f"진행 중: {chunk.get('message')}")
                            elif chunk.get("status") == "error":
                                progress_container.error(f"오류: {chunk.get('message')}")
                                st.error("대화 생성 중 오류 발생. 서버 로그를 확인해주세요.")
                                break
                            elif chunk.get("status") == "complete":
                                progress_container.success(chunk.get("message"))
                                break
                            else: # Actual conversation data chunk
                                st.session_state.full_report_data.append(chunk)
                                with report_placeholder.container():
                                    render_conversations_report(st.session_state.full_report_data)
                                # Force a rerun to update the UI with new data.
                                # This is necessary for real-time updates in Streamlit during streaming.
                                st.rerun()

                        except json.JSONDecodeError as e:
                            progress_container.error(f"서버 응답 디코딩 오류: {e}. 유효하지 않은 JSON. 줄: {decoded_line}")
                            break
                        except Exception as e:
                            progress_container.error(f"스트림 청크 처리 중 예상치 못한 오류: {e}")
                            break

        except requests.exceptions.Timeout:
            progress_container.error("FastAPI 서버 응답 시간 초과. LM Studio 서버 상태 및 네트워크 연결을 확인해주세요.")
        except requests.exceptions.ConnectionError:
            progress_container.error(f"FastAPI 서버에 연결할 수 없습니다. 서버가 {FASTAPI_URL}에서 실행 중인지 확인해주세요.")
        except requests.exceptions.RequestException as e:
            progress_container.error(f"요청 중 오류 발생: {e}")
            st.write(f"상세 오류: {e}")
        except Exception as e:
            progress_container.error(f"예상치 못한 오류 발생: {e}")
        finally:
            st.session_state.is_generating = False

# --- UI Update and Download/Save Buttons ---
if st.session_state.full_report_data:
    person_name_for_display = st.session_state.person_name_input_value if st.session_state.person_name_input_value else "unknown"

    render_conversations_report(st.session_state.full_report_data)

    col1, col2 = st.columns(2)
    with col1:
        json_str_for_download = json.dumps(st.session_state.full_report_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="전체 리포트 (클라이언트에서) JSON 파일 다운로드",
            data=json_str_for_download,
            file_name=f"dialogue_report_with_emotions_{person_name_for_display}_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json",
            help="생성된 대화 데이터를 브라우저를 통해 직접 JSON 파일로 다운로드합니다."
        )
    with col2:
        if st.button("전체 리포트 (서버에) JSON 파일 저장", help="생성된 대화 데이터를 FastAPI 서버에 저장합니다."):
            save_endpoint = f"{FASTAPI_URL}/save-conversations/"
            try:
                save_response = requests.post(save_endpoint, json={"data": st.session_state.full_report_data}, timeout=60)
                save_response.raise_for_status()
                save_result = save_response.json()
                st.success(save_result.get("message", "파일이 성공적으로 저장되었습니다."))
                if "file_path" in save_result:
                    st.info(f"저장된 경로: {save_result['file_path']}")
            except requests.exceptions.RequestException as e:
                st.error(f"서버에 파일 저장 요청 중 오류 발생: {e}")
            except Exception as e:
                st.error(f"파일 저장 처리 중 예상치 못한 오류 발생: {e}")

    st.success("모든 대화문 생성이 완료되었습니다.")
elif not st.session_state.is_generating and submitted:
    st.warning("생성된 대화 데이터가 없거나 오류가 발생했습니다. 조건을 다시 확인해주세요.")