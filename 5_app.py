import ollama

def stream_chat():
    stream = ollama.chat(
        model='gemma3:12b',
        messages=[
            {
                'role': 'system',
                'content': (
                    "당신은 감정 공감형 챗봇 학습 데이터를 생성하는 데이터 생성자입니다. "
                    "각 대화는 가상의 인물 간의 현실적인 한국어 대화여야 하며, 인물의 연령대(청소년, 성인, 노년층), 성별(남성, 여성), 감정(예: 기쁨, 슬픔, 불안, 설렘 등)이 명확하게 드러나야 합니다. "
                    "응답은 반드시 JSON 형식으로만 출력하세요. 키는 age_group, gender, emotion, role, content입니다. "
                    "설명이나 부연 없이 JSON만 출력하세요."
                )
            },
            {
                'role': 'user',
                'content': (
                    "챗봇 학습 데이터로 사용할 수 있는 대화 예시 한 개를 생성해 주세요. "
                    "인물의 연령대, 성별, 감정을 반드시 명시해 주세요."
                )
            }
        ],
        stream=True
    )

    # 실시간으로 생성되는 대화 내용을 출력
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)

stream_chat()
