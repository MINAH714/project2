import streamlit as st # Streamlit 라이브러리 임포트
import boto3 # AWS S3 접근을 위한 boto3 라이브러리 임포트
import json # JSON 데이터 처리를 위한 json 라이브러리 임포트
import pandas as pd # 데이터 처리를 위한 pandas 라이브러리 임포트
from collections import defaultdict # 감정 카운트를 위한 defaultdict 임포트
from dotenv import load_dotenv # .env 파일 로드를 위한 dotenv 임포트
import os # 환경 변수 접근을 위한 os 임포트
# Altair 라이브러리 임포트를 제거합니다.
# import altair as alt 

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- S3 설정 (실제 값으로 변경 필요) ---
S3_BUCKET_NAME = "kibwa-12"  # 여기에 실제 S3 버킷 이름을 입력하세요!
S3_FILE_KEY = "dummy/Winter_all/Winter_female_18_d3929dfc.json"  # 여기에 S3 파일 경로 (키)를 입력하세요!

# 대화 분석 대상 인물 및 감정 목록
TARGET_PERSON_NAME = "Winter"
ALL_EMOTIONS = ["기쁨", "분노", "슬픔", "두려움", "놀람"]

# --- 감정별 색상 정의 ---
EMOTION_COLORS = {
    "기쁨": "#FFE893",  
    "분노": "#CDC1FF",  
    "슬픔": "#F5F0CD",  
    "두려움": "#FFD6BA", 
    "놀람": "#9EC6F3"  
}
# chart_colors 리스트는 st.bar_chart에서 사용하기 위해 유지합니다.
chart_colors = [EMOTION_COLORS[emotion] for emotion in ALL_EMOTIONS]


# --- S3에서 JSON 불러오는 함수 ---
@st.cache_data # Streamlit 캐싱을 사용하여 데이터를 효율적으로 로드
def load_json_from_s3(bucket_name: str, file_key: str):
    """S3에서 JSON 파일을 불러와 파이썬 객체로 반환합니다."""
    s3 = boto3.client("s3")
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response["Body"].read().decode("utf-8")
        json_data = json.loads(file_content)
        st.success(f"S3에서 '{file_key}' 파일을 성공적으로 불러왔습니다.")
        return json_data
    except Exception as e:
        st.error(f"S3에서 파일을 불러오는 중 오류 발생: {e}. "
                 f"S3 버킷 이름, 파일 키, AWS 자격 증명(.env 파일) 및 S3 CORS 설정을 확인해주세요.")
        return None

# --- 특정 인물의 날짜별 감정 데이터 추출 함수 ---
def extract_person_emotions_by_date(data: list, person_name: str, emotions_list: list):
    """
    JSON 데이터에서 특정 인물의 날짜별 감정 발화 횟수를 추출합니다.
    """
    emotion_counts_by_date = defaultdict(lambda: defaultdict(int))
    
    if not data:
        return []

    for entry in data:
        timestamp = entry.get('timestamp')
        entry_person_name = entry.get('person_name')

        if timestamp and entry_person_name == person_name:
            for utterance in entry.get('conversation', []):
                if utterance.get('speaker') == person_name and utterance.get('emotions'):
                    for emotion in utterance['emotions']:
                        if emotion in emotions_list:
                            emotion_counts_by_date[timestamp][emotion] += 1
    
    processed_data = []
    # 타임스탬프를 기준으로 정렬하여 일관된 순서 보장
    sorted_dates = sorted(emotion_counts_by_date.keys())

    for date in sorted_dates:
        date_data = {"timestamp": date}
        for emotion in emotions_list:
            date_data[emotion] = emotion_counts_by_date[date][emotion]
        processed_data.append(date_data)
    
    return processed_data


# --- Streamlit 앱 메인 로직 시작 ---
st.set_page_config(layout="wide", page_title=f"감정 변화 분석기 - {TARGET_PERSON_NAME}")

# --- 사이드바 디자인 변경 (이 부분만 수정) ---
with st.sidebar:
    st.header("✨ **메뉴**") # 메뉴 제목을 좀 더 강조
    st.markdown("---") # 시각적 구분선

    # CSS를 사용하여 버튼처럼 보이는 링크 스타일 적용
    st.markdown("""
    <style>
    .button-link {
        display: block; /* 블록 요소로 만들어 전체 너비를 차지하게 함 */
        text-decoration: none; /* 밑줄 제거 */
        color: white; /* 텍스트 색상 */
        background-color: white; /* 버튼 배경색 (기존 nav-link-selected 색상 사용) */
        padding: 10px 20px; /* 버튼 내부 패딩 */
        border-radius: 8px; /* 둥근 모서리 */
        text-align: left; /* 텍스트 왼쪽 정렬 */
        margin-bottom: 10px; /* 버튼 간 간격 */
        font-weight: bold; /* 텍스트 굵게 */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* 은은한 그림자 */
        transition: background-color 0.3s ease; /* 호버 시 부드러운 전환 효과 */
    }
    .button-link:hover {
        background-color: #78B3CE; /* 호버 시 색상 변경 */
    }
    </style>
    """, unsafe_allow_html=True)

    # 각 메뉴 항목을 HTML <a> 태그로 만들고, 위에 정의한 스타일 적용
    # 현재 페이지의 경로를 가져와서 'Report' 링크를 클릭한 것과 동일한 효과를 내기 위해
    # Streamlit의 쿼리 파라미터를 사용할 수 있으나, 여기서는 단순히 링크만 제공합니다.
    # 실제 Streamlit 페이지 전환 로직은 Streamlit의 멀티페이지 앱 기능을 사용해야 합니다.
    # 이 예시에서는 외부 링크로 처리합니다.
    st.markdown('<a href="https://www.example.com/dummy" target="_blank" class="button-link">🔗 Dummy</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://aws.amazon.com/s3/" target="_blank" class="button-link">☁️ S3</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://www.example.com/chatbot" target="_blank" class="button-link">🤖 Chatbot</a>', unsafe_allow_html=True)
    # Report 링크를 클릭하면 현재 페이지로 돌아오는 동작을 구현하는 것은
    # Streamlit의 아키텍처 상 단순한 HTML 링크로는 어렵습니다.
    # 여기서는 임시적으로 placeholder URL을 사용합니다.
    st.markdown('<a href="#" class="button-link">📄 Report</a>', unsafe_allow_html=True) 

    st.markdown("---") # 시각적 구분선
    st.info("이 앱은 'Winter'의 감정 변화를 분석합니다.")

# --- 메인 콘텐츠 영역 (선택된 메뉴에 따라 달라짐) ---
# 기존 option_menu의 'choice' 변수를 더 이상 사용하지 않으므로,
# 모든 로직은 Report 페이지에 해당하는 것으로 가정하고 직접 실행합니다.
st.title(f'💬 {TARGET_PERSON_NAME}의 감정 변화 분석')
st.markdown("이 앱은 S3에서 대화 데이터를 불러와 특정 인물의 날짜별 감정 변화를 시각화합니다.")

# 1. S3 데이터 로드
st.subheader("데이터 로드 중...")
full_s3_data = load_json_from_s3(S3_BUCKET_NAME, S3_FILE_KEY)

if full_s3_data:
    st.success("데이터 로드 및 파싱 완료!")
    
    # 2. 'Winter'의 감정 데이터 추출
    st.subheader(f"📊 {TARGET_PERSON_NAME}의 감정 데이터 추출")
    winter_emotion_data = extract_person_emotions_by_date(full_s3_data, TARGET_PERSON_NAME, ALL_EMOTIONS)

    if winter_emotion_data:
        df = pd.DataFrame(winter_emotion_data)
        
        # 'timestamp' 컬럼을 datetime 객체로 변환
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # X축을 '요일변화'로 표시하기 위해 날짜와 요일을 함께 포함한 컬럼 생성
        # 예: 06-01 (일), 06-02 (월)
        korean_weekdays_short = ["월", "화", "수", "목", "금", "토", "일"]
        df['X축_요일변화'] = df['timestamp'].dt.strftime('%m-%d (') + \
                             df['timestamp'].dt.weekday.apply(lambda x: korean_weekdays_short[x]) + ')'

        # --- 데이터프레임과 그래프를 두 개의 컬럼으로 분할하여 표시 ---
        col_df, col_chart = st.columns([0.4, 0.6]) # 왼쪽 40%, 오른쪽 60% 비율로 컬럼 생성

        with col_df:
            # 데이터 미리보기 (왼쪽 컬럼)
            st.write("다음은 추출된 'Winter'의 날짜별 감정 발화 횟수 데이터입니다:")
            # 표시할 컬럼 순서 조정: 요일변화를 가장 앞에
            display_columns = ['X축_요일변화'] + ALL_EMOTIONS
            st.dataframe(df[display_columns])
        
        with col_chart:
            # --- Streamlit 내장 차트 사용 (오른쪽 컬럼) ---
            st.subheader(f"{TARGET_PERSON_NAME} 감정 변화 추이") # 차트 제목 변경
            st.markdown("**X축**: 요일변화, **Y축**: 갯수") # X, Y축 설명

            # Streamlit st.bar_chart를 위한 DataFrame 준비
            # X축으로 사용할 컬럼('X축_요일변화')을 인덱스로 설정하고, 감정 컬럼들만 남깁니다.
            df_for_chart = df.set_index('X축_요일변화')[ALL_EMOTIONS]
            
            # st.bar_chart 호출
            # `color` 인자를 사용하여 감정별 색상 커스터마이징을 시도합니다.
            # 여기서는 ALL_EMOTIONS의 순서와 EMOTION_COLORS의 값 순서가 일치하도록 리스트를 생성합니다.
            
            # 그래프 크기를 작게 만들기 위해 width와 height를 직접 지정합니다.
            # use_container_width=True를 제거하고 고정 크기를 설정합니다.
            st.bar_chart(df_for_chart, width=600, height=400, color=chart_colors)
            
    else:
        st.warning(f"'{TARGET_PERSON_NAME}'의 감정 데이터를 추출하지 못했습니다. S3 파일의 형식을 확인해주세요.")
else:
    st.info("S3에서 데이터를 로드할 수 없어 그래프를 표시할 수 없습니다. 위의 오류 메시지를 확인해주세요.")
