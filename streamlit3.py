import streamlit3 as st
import boto3
import os
import json
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'kibwa-12'

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# S3에서 JSON 파일을 읽는 함수
def load_json_from_s3(s3_key):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    return json.loads(obj['Body'].read().decode('utf-8'))

# 카테고리와 S3 경로 매핑
category_files = {
    "청소년 여성 학교생활": "project/teenage_female_school.json",
    "성인 남성 직장생활": "project/adult_male_work.json",
    "노년층 남성 일상": "project/elderly_male_daily.json"
}

# Streamlit UI
st.title("카테고리별 감정 데이터 리포트")

category = st.selectbox("카테고리를 선택하세요", list(category_files.keys()))

if st.button("리포트 보기"):
    try:
        data = load_json_from_s3(category_files[category])
        st.subheader(f"{category} 리포트")
        st.json(data)
    except Exception as e:
        st.error(f"데이터를 불러오는 데 실패했습니다: {e}")
