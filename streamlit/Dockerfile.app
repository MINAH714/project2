# Step 1: Python 3.9-slim-buster 기반 이미지 사용
FROM python:3.9-slim

# Step 2: 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# Step 3: 필요한 Python 라이브러리 설치를 위한 requirements.txt 복사 및 설치
# app.py에 필요한 Streamlit, requests 등이 포함되어야 합니다.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Step 4: app.py 애플리케이션 코드 복사
COPY . .

# Step 5: 애플리케이션이 리스닝할 포트 노출
EXPOSE 8501

# Step 6: 애플리케이션 실행 명령어
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
