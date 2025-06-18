import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta # datetime과 timedelta 추가

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

        request_payload = {
            "person_name": name, # FastAPI와 일치하도록 person_name으로 변경
            "age": age,
            "gender": gender,
            "situation": situation,
            "start_timestamp": start_date_str, # FastAPI와 일치하도록 start_timestamp로 변경
            "step_days": step_days,
            "num_conversations": num_dialogues_per_step # FastAPI와 일치하도록 num_conversations으로 변경
        }

        # FastAPI 엔드포인트 URL
        fastapi_endpoint_url = f"{FASTAPI_URL}/generate_conversation/" # FastAPI와 일치하도록 엔드포인트 변경

        try:
            # POST 요청 보내기
            response = requests.post(fastapi_endpoint_url, json=request_payload, timeout=300) # 5분 타임아웃
            response.raise_for_status() # HTTP 오류가 발생하면 예외 발생

            result_data = response.json()

            if result_data: # FastAPI는 이제 성공/실패 JSON을 직접 반환하지 않고, 데이터를 반환함
                st.subheader("생성된 대화 리포트")
                st.markdown("---")

                # 각 날짜별 대화 데이터를 표시
                for entry in result_data: # FastAPI가 반환하는 리스트를 순회
                    st.markdown(f"### 날짜: **{entry.get('timestamp', '날짜 정보 없음')}**")
                    st.write(f"**이름:** {entry.get('person_name', '')}, **나이:** {entry.get('age', '')}, **성별:** {entry.get('gender', '')}, **상황:** {entry.get('situation', '')}")
                    st.markdown("#### 대화 목록:")
                    
                    # 대화 발화 목록 표시
                    if entry.get('conversation'): # 'conversation' 키 사용
                        for dialogue_item in entry['conversation']:
                            speaker = dialogue_item.get('speaker', '알 수 없음')
                            content = dialogue_item.get('content', '')
                            emotions = dialogue_item.get('emotions', [])
                            emotions_str = f" (감정: {', '.join(emotions)})" if emotions else ""
                            # 시간 정보는 LM Studio에서 추출된 것이므로, 없으면 생략
                            st.write(f"- **{speaker}:** {content}{emotions_str}")
                    else:
                        st.write("해당 날짜에 생성된 대화가 없습니다.")
                    st.markdown("---")

                # 전체 JSON 데이터 다운로드 버튼
                json_str = json.dumps(result_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="전체 리포트 (감정 포함) JSON 파일 다운로드",
                    data=json_str,
                    file_name=f"dialogue_report_with_emotions_{name}_{date.today().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

                st.success("대화문 생성이 완료되었습니다. 다운로드 버튼을 클릭하여 데이터를 확인하세요.")
            else:
                st.error(f"대화문 생성 실패: FastAPI 서버로부터 빈 응답을 받았습니다.")
                st.json(result_data) # 혹시라도 에러 메시지가 있을 경우 출력

        except requests.exceptions.Timeout:
            st.error("FastAPI 서버 응답 시간이 초과되었습니다. LM Studio 서버 상태 및 네트워크 연결을 확인해주세요.")
        except requests.exceptions.ConnectionError:
            st.error(f"FastAPI 서버에 연결할 수 없습니다. 서버가 {FASTAPI_URL}에서 실행 중인지 확인해주세요.")
        except requests.exceptions.RequestException as e:
            st.error(f"요청 중 오류가 발생했습니다: {e}")
            st.write(f"상세 오류: {e}")
        except json.JSONDecodeError:
            st.error("FastAPI 서버로부터 유효하지 않은 JSON 응답을 받았습니다. 서버 로그를 확인해주세요.")
        except Exception as e:
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")