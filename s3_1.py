import os
import boto3
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'kibwa-12'

files_to_upload = {
    'adolescent_female_daily.json': 'project/adolescent_female_daily.json',
    'adult_male_daily.json': 'project/adult_male_daily.json',
    'elderly_male_daily.json': 'project/elderly_male_daily.json'
}

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# 파일 업로드
for local_file, s3_key in files_to_upload.items():
    s3.upload_file(local_file, BUCKET_NAME, s3_key)
    print(f"{local_file} → S3://{BUCKET_NAME}/{s3_key} 업로드 완료")
