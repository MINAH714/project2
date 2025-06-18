import streamlit as st
import requests
import json
import random
from datetime import date, datetime, timedelta # datetime 임포트 추가

# Streamlit 앱 제목
st.title("AI 공감형 대화문 생성기")

# 파라미터 입력 폼
name = st.selectbox("이름", ["Alice", "Peter", "Sue"])
age = st.number_input("나이", min_value=13, max_value=100, value=17)
gender = st.radio("성별", ["male", "female"])

# 나이에 따른 상황 옵션 동적 변경
situation_options = {
    "teenager": ["학교 생활", "감정 변화", "취미 및 여가 활동 탐색"],
    "adult_young": ["사회 초년생", "인간관계 및 독립", "자기개발"],
    "adult_middle": ["가정", "직장생활", "건강 관리"],
    "senior": ["은퇴 및 여가 생활", "건강 관리", "사회적 고립"]
}

def get_age_group(age_val):
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

# 'not_target' 그룹에 대한 기본 상황 처리 (예외 방지)
if age_group_val == "not_target":
    st.warning("13세 미만은 대화 생성 대상이 아닙니다.")
    situation = None # 상황을 선택할 수 없도록 설정
else:
    situation = st.selectbox("상황", situation_options[age_group_val])

# 추가 파라미터: Step (일), 갯수
start_date_str = "2025-06-01" # 타임스탬프 기준 시작일
start_date = date.fromisoformat(start_date_str)

step_days = st.number_input("Step (일 간격)", min_value=1, value=3) 
num_dialogues_per_step = st.number_input("회차 (날짜) 갯수", min_value=1, value=4) # 이전에 '회차당 대화 갯수'였으나, '회차(날짜) 갯수'로 의미 변경

# 'AI 대화문 생성' 버튼
if st.button("AI 대화문 생성"):
    if situation is None:
        st.error("나이 그룹에 해당하는 상황을 선택해주세요.")
    else:
        st.info("AI 대화문을 생성 중입니다. 잠시 기다려 주세요...")

        # FastAPI 서버로 요청 보낼 데이터 준비
        request_payload = {
            "name": name,
            "age": age,
            "gender": gender,
            "situation": situation,
            "start_date": start_date_str,
            "step_days": step_days,
            "num_dialogues_per_step": num_dialogues_per_step
        }

        # FastAPI 엔드포인트 URL (로컬에서 실행 시)
        fastapi_url = "http://localhost:8000/generate_dialogues" 

        try:
            response = requests.post(fastapi_url, json=request_payload, timeout=300) 
            response.raise_for_status() 

            result_data = response.json()

            if result_data.get("status") == "success":
                generated_report_data = result_data.get("data", [])
                st.subheader("생성된 대화 리포트")

                for entry in generated_report_data:
                    st.markdown(f"### 날짜: **{entry['date']}**")
                    st.write(f"**이름:** {entry['name']}, **나이:** {entry['age']}, **성별:** {entry['gender']}, **상황:** {entry['situation']}")
                    st.markdown("#### 대화 목록:")
                    
                    if entry.get('daily_dialogues'):
                        for dialogue_item in entry['daily_dialogues']:
                            st.write(f"- [{dialogue_item['time']}] {dialogue_item['dialogue_text']}")
                    else:
                        st.write("해당 날짜에 생성된 대화가 없습니다.")
                    st.markdown("---") # 각 날짜별 대화 사이에 구분선 추가

                # 전체 리포트를 하나의 JSON 파일로 다운로드
                json_str = json.dumps(generated_report_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="전체 리포트 JSON 파일 다운로드",
                    data=json_str,
                    file_name=f"dialogue_report_{name}_{date.today().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            else:
                st.error(f"대화문 생성 실패: {result_data.get('message', '알 수 없는 오류')}")
                if "error_details" in result_data:
                    st.json(result_data["error_details"])

        except requests.exceptions.Timeout:
            st.error("FastAPI 서버 응답 시간이 초과되었습니다. LM Studio 서버 상태를 확인해주세요.")
        except requests.exceptions.ConnectionError:
            st.error("FastAPI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        except requests.exceptions.RequestException as e:
            st.error(f"요청 중 오류가 발생했습니다: {e}")
            st.write("FastAPI 서버 로그를 확인해주세요.")
        except json.JSONDecodeError:
            st.error("FastAPI 서버로부터 유효하지 않은 JSON 응답을 받았습니다. 서버 로그를 확인해주세요.")
        except Exception as e:
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")