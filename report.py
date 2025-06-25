import boto3
import json
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import io # BytesIO for reading from S3

# --- S3 설정 ---
S3_BUCKET_NAME = "kibwa-12"  # 여기에 S3 버킷 이름을 입력하세요
S3_FILE_KEY = "dummy/winter    # 여기에 S3 파일 경로 (키)를 입력하세요

def load_json_from_s3(bucket_name: str, file_key: str):
    """S3에서 JSON 파일을 불러와 파이썬 객체로 반환합니다."""
    s3 = boto3.client("s3")
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response["Body"].read().decode("utf-8")
        json_data = json.loads(file_content)
        print(f"S3에서 '{file_key}' 파일을 성공적으로 불러왔습니다.")
        return json_data
    except Exception as e:
        print(f"S3에서 파일을 불러오는 중 오류 발생: {e}")
        raise

# S3에서 데이터 불러오기
try:
    s3_data = load_json_from_s3(S3_BUCKET_NAME, S3_FILE_KEY)
except Exception as e:
    print(f"오류: S3에서 데이터를 불러오지 못했습니다. 설정(버킷 이름, 파일 키, AWS 자격 증명)을 확인해주세요.")
    exit() # 스크립트 종료

# --- 감정 추출 및 집계 ---
def extract_winter_emotions_by_date(data: list, target_person_name: str = "Winter"):
    """
    JSON 데이터에서 특정 인물의 날짜별 감정 발화 횟수를 추출합니다.
    """
    emotion_counts_by_date = defaultdict(lambda: defaultdict(int))
    # 코드 내에서 사용된 감정 목록 (API 코드에서 정의된 EMOTIONS와 동일)
    all_emotions = ["기쁨", "분노", "슬픔", "두려움", "놀람"]

    for entry in data:
        timestamp = entry.get('timestamp')
        person_name_in_entry = entry.get('person_name')

        if timestamp and person_name_in_entry == target_person_name:
            for utterance in entry.get('conversation', []):
                # 'speaker'가 target_person_name인 경우만 집계
                if utterance.get('speaker') == target_person_name:
                    for emotion in utterance.get('emotions', []):
                        if emotion in all_emotions:
                            emotion_counts_by_date[timestamp][emotion] += 1
    
    # 누락된 감정은 0으로 채우고, 날짜를 기준으로 정렬
    processed_data = []
    # 날짜를 기준으로 정렬하기 위해 딕셔너리 키를 리스트로 변환 후 정렬
    sorted_dates = sorted(emotion_counts_by_date.keys())

    for date in sorted_dates:
        date_data = {"timestamp": date}
        for emotion in all_emotions:
            date_data[emotion] = emotion_counts_by_date[date][emotion]
        processed_data.append(date_data)

    print(f"'{target_person_name}'의 날짜별 감정 데이터 추출 완료.")
    return processed_data

# 'Winter'의 감정 데이터 추출
winter_emotion_data = extract_winter_emotions_by_date(s3_data, "Winter")

# 추출된 데이터 확인 (선택 사항)
print("\n--- 추출된 'Winter'의 날짜별 감정 데이터 ---")
for row in winter_emotion_data:
    print(row)

# --- 그래프 생성 ---
def plot_weekly_emotion_change(emotion_data: list, person_name: str = "Winter"):
    """
    날짜별 감정 데이터를 바탕으로 누적 막대 차트를 생성합니다.
    """
    if not emotion_data:
        print("그래프를 생성할 데이터가 없습니다.")
        return

    df = pd.DataFrame(emotion_data)
    
    # 'timestamp' 컬럼을 datetime 객체로 변환하여 정렬에 활용
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp')

    # 그래프를 그리기 위한 데이터프레임 재구성 (long format)
    # 'timestamp'를 제외한 감정 컬럼들만 선택
    emotions_columns = [col for col in df.columns if col not in ['timestamp']]
    df_melted = df.melt(id_vars=['timestamp'], value_vars=emotions_columns, 
                         var_name='Emotion', value_name='Count')

    plt.figure(figsize=(12, 7))
    
    # 누적 막대 차트 생성
    sns.barplot(x='timestamp', y='Count', hue='Emotion', data=df_melted, dodge=False)

    plt.title(f'{person_name}의 날짜별 감정 변화 (누적 막대 차트)', fontsize=16)
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('감정 발화 횟수', fontsize=12)
    plt.xticks(rotation=45, ha='right') # 날짜 라벨 회전
    plt.legend(title='감정')
    plt.tight_layout() # 레이아웃 조정
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.show()
    print("그래프 생성이 완료되었습니다.")

# 그래프 생성 함수 호출
plot_weekly_emotion_change(winter_emotion_data, "Winter")