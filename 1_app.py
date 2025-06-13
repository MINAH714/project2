import ollama

# 감정별 대화 시나리오 생성 요청 프롬프트
prompt = """
슬픈 감정을 가진 10대 여성(중·고등학생) 페르소나와의 대화 시나리오를 100개 이상 생성해주세요.
각 대화는 짧은 질문/답변 한 쌍으로 구성해 주세요.
예시:
- 사용자: 오늘 학교에서 친구랑 싸웠어.
- 챗봇: 힘들었겠다. 이야기 나눠줘서 고마워.
감정적으로 공감하는 답변이 포함되도록 해주세요.
최종 결과는 JSON 형태로 감정(슬픔), 페르소나(10대 여성), 대화 목록(사용자 발화, 챗봇 답변)으로 구조화해 주세요.
"""

response = ollama.chat(
    model='gemma3:latest', 
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant for generating emotional dialogue scenarios.'},
        {'role': 'user', 'content': prompt}
    ]
)

print(response['message']['content'])