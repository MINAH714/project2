import streamlit as st # Streamlit 라이브러리 임포트
import boto3 # AWS S3 접근을 위한 boto3 라이브러리 임포트
import json # JSON 데이터 처리를 위한 json 라이브러리 임포트
import pandas as pd # 데이터 처리를 위한 pandas 라이브러리 임포트
from collections import defaultdict # 감정 카운트를 위한 defaultdict 임포트
from dotenv import load_dotenv # .env 파일 로드를 위한 dotenv 임포트
import os # 환경 변수 접근을 위한 os 임포트

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- S3 설정 (실제 값으로 변경 필요) ---
S3_BUCKET_NAME = "kibwa-12"  # 여기에 실제 S3 버킷 이름을 입력하세요!
S3_FILE_KEY = "dummy/Winter_all/Winter_female_18_d3929dfc.json"  # 여기에 S3 파일 경로 (키)를 입력하세요!

# 대화 분석 대상 인물 및 감정 목록
TARGET_PERSON_NAME = "Winter"
ALL_EMOTIONS = ["기쁨", "분노", "슬픔", "두려움", "놀람"]

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

# --- 감정별 색상 정의 ---
EMOTION_COLORS = {
    "기쁨": "#FFE893",  # 밝은 노랑
    "분노": "#CDC1FF",  # 강렬한 빨강
    "슬픔": "#F5F0CD",  # 하늘색
    "두려움": "#FFD6BA", # 진회색
    "놀람": "#9EC6F3"   # 연보라
}

# --- Streamlit 앱 메인 로직 시작 ---
st.set_page_config(layout="wide", page_title=f"감정 변화 분석기 - {TARGET_PERSON_NAME}")

# --- 사이드바 추가 ---
with st.sidebar:
    st.header("메뉴")
    st.markdown("[Dummy](https://www.example.com/dummy)") # 예시 URL
    st.markdown("[S3](https://aws.amazon.com/s3/)") # 예시 URL
    st.markdown("[Chatbot](https://www.example.com/chatbot)") # 예시 URL
    st.markdown("[Report](https://www.example.com/report)") # 예시 URL
    st.markdown("---")
    st.info("이 앱은 'Winter'의 감정 변화를 분석합니다.")

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

        # 데이터 미리보기
        st.write("다음은 추출된 'Winter'의 날짜별 감정 발화 횟수 데이터입니다:")
        # 표시할 컬럼 순서 조정: 요일변화를 가장 앞에
        display_columns = ['X축_요일변화'] + ALL_EMOTIONS
        st.dataframe(df[display_columns])

        # --- Streamlit 내장 차트만 사용 ---
        st.subheader(f"{TARGET_PERSON_NAME}") # 차트 제목: Winter
        st.markdown("**X축**: 요일변화, **Y축**: 갯수") # X, Y축 설명

        # Streamlit st.bar_chart를 위한 DataFrame 준비
        # X축으로 사용할 컬럼('X축_요일변화')을 인덱스로 설정하고, 감정 컬럼들만 남깁니다.
        df_for_chart = df.set_index('X축_요일변화')[ALL_EMOTIONS]
        
        # st.bar_chart 호출
        # `color` 인자를 사용하여 감정별 색상 커스터마이징을 시도합니다.
        # 여기서는 ALL_EMOTIONS의 순서와 EMOTION_COLORS의 값 순서가 일치하도록 리스트를 생성합니다.
        chart_colors = [EMOTION_COLORS[emotion] for emotion in ALL_EMOTIONS]

        # 그래프 크기를 작게 만들기 위해 width와 height를 직접 지정합니다.
        # use_container_width=True를 제거하고 고정 크기를 설정합니다.
        st.bar_chart(df_for_chart, width=600, height=400, color=chart_colors)

        st.info("💡 **참고:** Streamlit 내장 차트는 Y축 제목을 직접 설정하는 기능이 제한적입니다. Y축의 높이는 감정 발화의 '갯수'를 나타내며, 각 색상 블록은 해당 감정의 갯수를 의미합니다.")
        
    else:
        st.warning(f"'{TARGET_PERSON_NAME}'의 감정 데이터를 추출하지 못했습니다. S3 파일의 형식을 확인해주세요.")
else:
    st.info("S3에서 데이터를 로드할 수 없어 그래프를 표시할 수 없습니다. 위의 오류 메시지를 확인해주세요.")
