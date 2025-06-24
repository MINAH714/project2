# Step 1: Node.js 18-alpine 기반 이미지 사용 (경량 이미지)
FROM node:18-alpine

# Step 2: 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# Step 3: package.json 복사 및 의존성 설치
# package.json에 정의된 pm2를 포함한 모든 의존성을 설치합니다.
COPY package.json .
RUN npm install

# Step 4: 애플리케이션 코드 복사
# server.js (이전 main.js), index.html, login.html 파일을 복사합니다.
COPY main.js .
COPY index.html .
COPY login.html .
COPY report.html .
# 추가적으로 필요한 정적 자원(CSS, JS, 이미지 등)이 있다면 해당 디렉토리를 복사합니다.
# 예: COPY public/ ./public/

# Step 5: 애플리케이션이 리스닝할 포트 노출
# server.js에서 3000번 포트를 사용하므로, 3000번을 노출합니다.
EXPOSE 3000

# Step 6: 애플리케이션 실행 명령어 (PM2 사용)
# pm2-runtime은 Docker 환경에 최적화된 PM2 실행 모드입니다.
CMD ["node", "main.js"]