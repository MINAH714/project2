import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta

# FastAPI 서버의 URL (FastAPI 서버가 8080 포트에서 실행될 것으로 가정)
FASTAPI_URL = "http://localhost:8080"

# Streamlit 앱 제목
st.title("AI 공감형 대화문 생성기")
st.markdown("---")
st.subheader("대화문 생성 조건 입력")

# 파라미터 입력 폼
name = st.selectbox("이름", ["Alice", "Peter", "Sue"])
age = st.number_input("나이", min_value=13, max_value=100, value=17)
gender = st.radio("성별", ["male", "female"])

# 나이에 따른 상황 옵션 동적 변경
situation_options_map = {
    "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색"],
    "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발"],
    "adult_middle": ["가정", "직장생활", "건강 관리"],
    "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립"]
}

def get_age_group(age_val):
    """나이에 따른 연령대 그룹 반환"""
    if 13 <= age_val <= 19:
        return "teenager"
    elif 20 <= age_val <= 39:
        return "adult_young"
    elif 40 <= age_val <= 65:
        return "adult_middle"
    elif age_val > 65:
        return "senior"
    else:
        return "not_target"

age_group_val = get_age_group(age)

if age_group_val == "not_target":
    st.warning("13세 미만은 대화 생성 대상이 아닙니다.")
    situation = None
else:
    situation = st.selectbox("상황", situation_options_map.get(age_group_val, []))

# 기준 타임스탬프 (기본값 2025-06-01, 사용자가 수정 가능)
start_date_input = st.date_input("기준 시작 날짜 (YYYY-MM-DD)", value=date(2025, 6, 1))
start_date_str = start_date_input.isoformat() # ISO 형식 문자열로 변환

step_days = st.number_input("Step (일 간격)", min_value=1, value=3)
num_dialogues_per_step = st.number_input("회차 (날짜) 갯수", min_value=1, value=4)

st.markdown("---")

# 'AI 대화문 생성' 버튼
if st.button("AI 대화문 생성"):
    if situation is None or not situation: # 상황이 선택되지 않았거나 비어있는 경우
        st.error("나이 그룹에 해당하는 상황을 선택해주세요.")
    else:
        st.info("AI 대화문을 생성 중입니다. 잠시 기다려 주세요...")

        # 진행 상황을 표시할 placeholder
        progress_container = st.empty()
        # 생성된 대화 리포트를 표시할 컨테이너
        report_placeholder = st.empty()
        full_report_data = [] # 전체 데이터를 저장할 리스트 (다운로드용)

        request_payload = {
            "person_name": name,
            "age": age,
            "gender": gender,
            "situation": situation,
            "start_timestamp": start_date_str,
            "step_days": step_days,
            "num_conversations": num_dialogues_per_step
        }

        # 스트리밍 엔드포인트 URL
        fastapi_endpoint_url = f"{FASTAPI_URL}/generate_conversation_stream/"

        try:
            # POST 요청 보내기 (stream=True로 스트리밍 활성화)
            with requests.post(fastapi_endpoint_url, json=request_payload, stream=True, timeout=300) as response:
                response.raise_for_status() # HTTP 오류가 발생하면 예외 발생

                # 각 줄(청크)을 읽어서 처리
                # iter_lines()는 '\n'을 기준으로 한 줄씩 읽어옴
                for line in response.iter_lines():
                    if line: # 빈 줄이 아니면 처리
                        decoded_line = line.decode('utf-8')
                        try:
                            chunk = json.loads(decoded_line)

                            # Streamlit에 진행 상황 업데이트
                            if chunk.get("status") == "generating":
                                progress_container.info(chunk.get("message"))
                            elif chunk.get("status") == "progress":
                                progress_container.text(chunk.get("message"))
                            elif chunk.get("status") == "error":
                                progress_container.error(chunk.get("message"))
                                st.error("대화 생성 중 오류 발생.")
                                break # 오류 발생 시 스트림 중단
                            elif chunk.get("status") == "complete":
                                progress_container.success(chunk.get("message"))
                                break # 완료 메시지 수신 시 스트림 중단
                            else: # 실제 대화 데이터 청크 (날짜별 대화 세트)
                                full_report_data.append(chunk)

                                # Streamlit에 현재까지 받은 데이터 업데이트
                                # with report_placeholder.container():를 사용하여 특정 영역만 업데이트
                                with report_placeholder.container():
                                    st.subheader("생성된 대화 리포트 (실시간 업데이트)")
                                    st.markdown("---")
                                    for entry in full_report_data:
                                        st.markdown(f"### 날짜: **{entry.get('timestamp', '날짜 정보 없음')}**")
                                        st.write(f"**이름:** {entry.get('person_name', '')}, **나이:** {entry.get('age', '')}, **성별:** {entry.get('gender', '')}, **상황:** {entry.get('situation', '')}")
                                        st.markdown("#### 대화 목록:")

                                        # 대화 발화 목록 표시
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

                                # Streamlit UI를 강제로 다시 렌더링하여 최신 데이터가 보이도록 함
                                # 이는 스트리밍 시 스크롤 문제 해결에 도움이 될 수 있음
                                # st.experimental_rerun() 대신 st.rerun() 사용 (Streamlit 1.14.0+ 권장)
                                st.rerun()

                        except json.JSONDecodeError as e:
                            # 내부 try 블록에서 JSON 디코딩 오류 발생 시 처리
                            st.error(f"FastAPI 서버로부터 유효하지 않은 JSON 응답을 받았습니다: {e}. 서버 로그를 확인해주세요. 디코딩된 줄: {decoded_line if 'decoded_line' in locals() else 'N/A'}")
                            break # JSON 파싱 오류 발생 시 스트림 처리 중단
                        except Exception as e:
                            # 내부 try 블록에서 발생한 기타 예외 처리
                            st.error(f"대화 청크 처리 중 예상치 못한 오류가 발생했습니다: {e}")
                            break # 오류 발생 시 스트림 처리 중단

        except requests.exceptions.Timeout:
            # 외부 try 블록에서 발생한 Timeout 예외 처리
            st.error("FastAPI 서버 응답 시간이 초과되었습니다. LM Studio 서버 상태 및 네트워크 연결을 확인해주세요.")
        except requests.exceptions.ConnectionError:
            # 외부 try 블록에서 발생한 ConnectionError 예외 처리
            st.error(f"FastAPI 서버에 연결할 수 없습니다. 서버가 {FASTAPI_URL}에서 실행 중인지 확인해주세요.")
        except requests.exceptions.RequestException as e:
            # 외부 try 블록에서 발생한 기타 RequestException 예외 처리
            st.error(f"요청 중 오류가 발생했습니다: {e}")
            st.write(f"상세 오류: {e}")
        except Exception as e:
            # 외부 try 블록에서 발생한 예상치 못한 기타 예외 처리
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")
        finally:
            # 스트림이 완료되거나 오류 발생 후 다운로드 버튼 표시
            if full_report_data:
                json_str = json.dumps(full_report_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="전체 리포트 (감정 포함) JSON 파일 다운로드",
                    data=json_str,
                    file_name=f"dialogue_report_with_emotions_{name}_{date.today().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
                st.success("대화문 생성이 완료되었습니다. 다운로드 버튼을 클릭하여 데이터를 확인하세요.")
            else:
                st.warning("생성된 대화 데이터가 없거나 오류가 발생했습니다.")
