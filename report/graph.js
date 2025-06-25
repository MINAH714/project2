document.addEventListener('DOMContentLoaded', async () => {
    // --- S3 파일 정보 설정 ---
    // 여기에 실제 S3 버킷 이름과 파일 키를 입력해주세요!
    const S3_BUCKET_NAME = "your-s3-bucket-name"; // 예: "my-conversation-data"
    const S3_FILE_KEY = "Winter_female_18.json"; // 예: "dialogues/Winter_female_18.json"

    // S3 퍼블릭 URL 생성 (리전이 다르면 URL 형식이 다를 수 있습니다)
    const S3_FILE_URL = `https://${S3_BUCKET_NAME}.s3.amazonaws.com/${S3_FILE_KEY}`;

    const targetPersonName = "Winter";
    const allEmotions = ["기쁨", "분노", "슬픔", "두려움", "놀람"];

    let winterEmotionProcessedData = {};

    try {
        // Step 1: S3에서 JSON 파일 불러오기 (fetch API 사용)
        console.log(`S3에서 데이터를 불러오는 중: ${S3_FILE_URL}`);
        const response = await fetch(S3_FILE_URL); 
        
        if (!response.ok) {
            // HTTP 오류 상태 코드 (4xx, 5xx) 처리
            throw new Error(`S3에서 JSON 파일을 불러오지 못했습니다. 상태: ${response.status}, 메시지: ${response.statusText}. CORS 설정을 확인해주세요.`);
        }
        const fullConversationsData = await response.json(); // JSON 내용을 파싱

        // Step 2: JSON 데이터에서 'Winter'의 감정 변화 데이터 추출
        fullConversationsData.forEach(entry => {
            const timestamp = entry.timestamp;
            const personNameInEntry = entry.person_name;

            if (timestamp && personNameInEntry === targetPersonName) {
                if (!winterEmotionProcessedData[timestamp]) {
                    winterEmotionProcessedData[timestamp] = {};
                    allEmotions.forEach(emotion => {
                        winterEmotionProcessedData[timestamp][emotion] = 0;
                    });
                }

                entry.conversation.forEach(utterance => {
                    if (utterance.speaker === targetPersonName && utterance.emotions) {
                        utterance.emotions.forEach(emotion => {
                            if (allEmotions.includes(emotion)) {
                                winterEmotionProcessedData[timestamp][emotion]++;
                            }
                        });
                    }
                });
            }
        });

        const sortedDates = Object.keys(winterEmotionProcessedData).sort();
        const chartDataArray = sortedDates.map(date => {
            return { timestamp: date, ...winterEmotionProcessedData[date] };
        });

        // Step 3: 추출된 데이터로 그래프 렌더링
        renderChart(chartDataArray, targetPersonName, allEmotions);

    } catch (error) {
        console.error('S3 데이터를 불러오거나 처리하는 중 오류 발생:', error);
        alert(`S3 데이터를 불러오거나 처리하는 중 오류가 발생했습니다: ${error.message}. S3 버킷의 CORS 설정과 파일 접근 권한을 확인해주세요.`);
    }

    // 그래프 렌더링 함수 (이전과 동일)
    function renderChart(dataToChart, personName, emotionsList) {
        if (!dataToChart || dataToChart.length === 0) {
            console.warn("그래프를 그릴 데이터가 없습니다.");
            return;
        }

        const labels = dataToChart.map(d => d.timestamp);
        const datasets = [];

        emotionsList.forEach(emotion => {
            const dataCounts = dataToChart.map(d => d[emotion] || 0);
            datasets.push({
                label: emotion,
                data: dataCounts,
                backgroundColor: getEmotionColor(emotion),
                borderColor: getEmotionColor(emotion),
                borderWidth: 1
            });
        });

        const ctx = document.getElementById('emotionChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar', // 누적 막대 차트
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: '날짜'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '감정 발화 횟수'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: `${personName}의 날짜별 감정 변화 (누적 막대 차트)`
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    // 감정별 색상 정의 함수 (이전과 동일)
    function getEmotionColor(emotion) {
        const colors = {
            "기쁨": 'rgba(255, 206, 86, 0.8)',
            "분노": 'rgba(255, 99, 132, 0.8)',
            "슬픔": 'rgba(54, 162, 235, 0.8)',
            "두려움": 'rgba(153, 102, 255, 0.82)',
            "놀람": 'rgba(102, 192, 75, 0.8)'
        };
        return colors[emotion] || 'rgba(128, 128, 128, 0.8)';
    }
});