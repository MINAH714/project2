import ollama
import json

def stream_generate_dialogues():
    persons = ["person1", "person2", "person3"]
    topics = ["학교생활", "가족", "친구관계", "취미", "진로"]
    emotions = ["기쁨", "슬픔", "불안", "설렘", "화남"]

    result = {}

    for person in persons:
        result[person] = {}
        for topic in topics:
            result[person][topic] = {}
            for emotion in emotions:
                prompt = f"""
아래 조건에 맞는 대화 시나리오를 생성해 주세요.
- age_group: 청소년
- gender: 여성
- emotion: {emotion}
- role: 학생
- topic: {topic}
각 대화는 짧은 질문/답변 한 쌍으로 구성해 주세요.
예시:
- 사용자: 오늘 학교에서 친구랑 싸웠어.
- 챗봇: 힘들었겠다. 이야기 나눠줘서 고마워.
감정적으로 공감하는 답변이 포함되도록 해주세요.
최종 결과는 JSON 형태로, 사용자 발화(user), 챗봇 답변(bot)을 포함해 주세요.
"""
                print(f"\n[Person: {person}, Topic: {topic}, Emotion: {emotion}]\n프롬프트: {prompt.strip()}\n생성 결과:")
                
                stream = ollama.chat(
                    model='gemma2:9b',
                    messages=[
                        {'role': 'system', 'content': 'You are a helpful assistant for generating emotional dialogue scenarios.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    stream=True
                )

                full_response = ''
                for chunk in stream:
                    content = chunk['message']['content']
                    print(content, end='', flush=True)  # 실시간 출력
                    full_response += content
                print("\n---")

                try:
                    dialog = json.loads(full_response)
                except Exception as e:
                    dialog = {"error": f"parsing failed: {str(e)}"}
                result[person][topic][emotion] = dialog

    # JSON 파일로 저장
    with open('dummy_conversations_stream.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("\n파일이 생성되었습니다: dummy_conversations_stream.json")

stream_generate_dialogues()
