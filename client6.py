import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta

# FastAPI 서버의 URL (main6.py의 uvicorn.run 설정에 맞춰 8000번 포트 사용)
FASTAPI_URL = "http://localhost:8080"

# --- Streamlit Session State 초기화 ---
# 이 부분을 추가하여 Streamlit 앱이 새로고침되거나 rerun될 때도 데이터가 유지되도록 합니다.
if 'full_report_data' not in st.session_state:
    st.session_state.full_report_data = []
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

# --- 대화 리포트 렌더링 함수 ---
# 함수 정의를 사용하기 전에 배치하여 NameError를 방지합니다.
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

# Streamlit 앱 제목
st.set_page_config(layout="wide") # 페이지 레이아웃을 넓게 설정
st.title("AI 공감형 대화문 생성기")
st.markdown("---")
st.subheader("대화문 생성 조건 입력")

# --- 파라미터 입력 폼 ---
with st.form("conversation_params_form"):
    name = st.selectbox("대화할 사람 이름", ["Alice", "Peter", "Sue", "Custom"], help="기본 이름 외에 'Custom'을 선택하여 직접 입력할 수 있습니다.")
    if name == "Custom":
        custom_name = st.text_input("직접 입력할 이름", value="새로운 인물")
        person_name_final = custom_name
    else:
        person_name_final = name

    age = st.number_input("나이", min_value=13, max_value=150, value=21)
    gender = st.radio("성별", ["male", "female"], horizontal=True)

    # 나이에 따른 상황 옵션 동적 변경 (FastAPI 서버의 SITUATION_OPTIONS에 맞춤)
    situation_options_map = {
        "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색", "일상 생활"],
        "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발", "일상 생활"],
        "adult_middle": ["가정", "직장생활", "건강 관리", "일상 생활"],
        "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립", "일상 생활"]
    }

    def get_age_group(age_val):
        """나이에 따른 연령대 그룹 반환"""
        if 13 <= age_val <= 19:
            return "teenager"
        elif 20 <= age_val <= 39:
            return "adult_young"
        elif 40 <= age_val <= 65:
            return "adult_middle"
        elif age_val >= 66: # 65세 이상으로 변경
            return "senior"
        else:
            return "not_target"

    age_group_val = get_age_group(age)

    if age_group_val == "not_target":
        st.warning("13세 미만은 대화 생성 대상이 아닙니다.")
        situation = None
    else:
        situation = st.selectbox("상황", situation_options_map.get(age_group_val, []), key="situation_select")
        if not situation and situation_options_map.get(age_group_val):
            st.error("나이 그룹에 해당하는 상황을 선택해주세요.") # 상황이 비어있을 경우 에러 표시

    # 기준 타임스탬프 (기본값 2025-06-01, 사용자가 수정 가능)
    start_date_input = st.date_input("기준 시작 날짜 (YYYY-MM-DD)", value=date(2025, 6, 1))
    start_date_str = start_date_input.isoformat() # ISO 형식 문자열로 변환

    step_days = st.number_input("Step (일 간격)", min_value=1, value=3)
    num_conversations = st.number_input("생성할 대화문 갯수 (회차)", min_value=1, value=4)

    st.markdown("---")
    
    # 'AI 대화문 생성' 버튼
    submitted = st.form_submit_button("AI 대화문 생성", disabled=st.session_state.is_generating)

# --- 대화 생성 로직 ---
if submitted:
    if situation is None or not situation: # 상황이 선택되지 않았거나 비어있는 경우
        st.error("상황을 선택하거나 유효한 나이를 입력하여 상황 옵션을 불러와 주세요.")
    else:
        st.session_state.is_generating = True
        st.session_state.full_report_data = [] # 새로운 생성 시작 시 데이터 초기화
        st.info("AI 대화문을 생성 중입니다. 잠시 기다려 주세요...")

        # 진행 상황을 표시할 placeholder
        progress_container = st.empty()
        # 생성된 대화 리포트를 표시할 컨테이너 (실시간 업데이트용)
        report_placeholder = st.empty()

        request_payload = {
            "person_name": person_name_final, # 커스텀 이름 반영
            "age": age,
            "gender": gender,
            "situation": situation,
            "start_timestamp": start_date_str,
            "step_days": step_days,
            "num_conversations": num_conversations
        }

        # 스트리밍 엔드포인트 URL (FastAPI 서버의 새 엔드포인트 이름 반영)
        fastapi_stream_endpoint = f"{FASTAPI_URL}/generate-stream/"

        try:
            with requests.post(fastapi_stream_endpoint, json=request_payload, stream=True, timeout=300) as response:
                response.raise_for_status() # HTTP 오류가 발생하면 예외 발생

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        try:
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
                                break # 완료 메시지 수신 시 스트림 중단
                            else: # 실제 대화 데이터 청크
                                st.session_state.full_report_data.append(chunk)
                                # 세션 상태 업데이트 후 UI 다시 그리기 함수 호출
                                with report_placeholder.container():
                                    render_conversations_report(st.session_state.full_report_data)
                                    # Streamlit의 UI 업데이트를 트리거 (필요한 경우만 사용)
                                    # st.rerun() # 전체 앱을 다시 시작하므로 스트리밍에는 권장되지 않음
                                    # st.experimental_rerun() # deprecated

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
            st.session_state.is_generating = False # 생성 완료 또는 오류 발생 시 버튼 활성화

# --- UI 업데이트 및 다운로드/저장 버튼 ---
# 생성 완료 후 또는 새로고침 시 이 부분이 항상 실행되어 UI를 그립니다.
if st.session_state.full_report_data:
    render_conversations_report(st.session_state.full_report_data)

    col1, col2 = st.columns(2)
    with col1:
        # 클라이언트에서 직접 JSON 파일 다운로드
        json_str_for_download = json.dumps(st.session_state.full_report_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="전체 리포트 (클라이언트에서) JSON 파일 다운로드",
            data=json_str_for_download,
            file_name=f"dialogue_report_with_emotions_{person_name_final}_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json",
            help="생성된 대화 데이터를 브라우저를 통해 직접 JSON 파일로 다운로드합니다."
        )
    with col2:
        # 서버에 JSON 파일 저장 요청
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
elif not st.session_state.is_generating and submitted: # 생성 버튼을 눌렀지만 데이터가 없는 경우 (오류 또는 생성 실패)
    st.warning("생성된 대화 데이터가 없거나 오류가 발생했습니다. 조건을 다시 확인해주세요.")