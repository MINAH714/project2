# Python 3.11 slim 이미지를 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 소스 복사
COPY streamlit3.py .

# 컨테이너 시작 시 Streamlit 실행
CMD ["streamlit", "run", "streamlit3.py", "--server.port=8501", "--server.headless=true"]
