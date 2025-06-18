# Python 공식 이미지 사용
FROM python:3.9-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 종속성 설치 (필요시)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# 종속성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY fastapi_server.py .

# 포트 노출 (FastAPI가 사용하는 포트)
EXPOSE 8080

# 애플리케이션 실행 명령어
CMD ["uvicorn", "fastapi_server:app", "--host", "0.0.0.0", "--port", "8080"]