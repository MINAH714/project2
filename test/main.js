// 필요한 Node.js 모듈 임포트
const http = require('http'); // HTTP 서버를 생성하기 위한 모듈
const fs = require('fs');   // 파일 시스템과 상호작용하기 위한 모듈
const path = require('path'); // 파일 경로를 다루기 위한 모듈

// 서버가 리스닝할 포트 설정
const port = 30000;

// HTTP 서버 생성
const server = http.createServer((req, res) => {
    // 요청된 URL에 따라 파일 경로 설정
    // 기본적으로 '/' 요청은 'index.html' 파일을 서빙
    let filePath = '.' + req.url;
    if (filePath === './') {
        filePath = './index.html';
    }

    // 파일 확장자 가져오기
    const extname = String(path.extname(filePath)).toLowerCase();
    // Content-Type 맵핑 (브라우저가 파일을 올바르게 해석하도록 돕기 위함)
    const mimeTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp'
    };

    // 요청된 파일의 Content-Type 설정
    const contentType = mimeTypes[extname] || 'application/octet-stream';

    // 파일 읽기
    fs.readFile(filePath, (error, content) => {
        if (error) {
            // 파일이 존재하지 않는 경우 (404 Not Found)
            if (error.code === 'ENOENT') {
                res.writeHead(404, { 'Content-Type': 'text/html' });
                res.end('<h1>404 Not Found</h1><p>The requested file was not found.</p>');
            } else {
                // 서버 내부 오류 (500 Internal Server Error)
                res.writeHead(500, { 'Content-Type': 'text/html' });
                res.end(`<h1>500 Internal Server Error</h1><p>Sorry, check with the site admin for error: ${error.code} ..\n</p>`);
            }
        } else {
            // 파일이 성공적으로 읽힌 경우 (200 OK)
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

// 서버 리스닝 시작
server.listen(port, () => {
    console.log(`Server running at http://localhost:${port}/`);
    console.log(`Open your browser and navigate to http://localhost:${port}/`);
});