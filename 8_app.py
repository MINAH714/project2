import ollama
import json

# 가상인물 및 감정 리스트
persons = [
    {"name": "청소년 여성 학교생활", "age_group": "청소년", "gender": "여성", "role": "학생", "topic": "학교생활"},
    {"name": "성인 남성 직장생활", "age_group": "성인", "gender": "남성", "role": "직장인", "topic": "직장생활"},
    {"name": "노년층 여성 일상", "age_group": "노년층", "gender": "여성", "role": "일상인", "topic": "일상"}
]
emotions = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]

result = {}

for person in persons:
    result[person['name']] = {}
    for emotion in emotions:
        dialogues = []
        for i in range(3):  # 샘플: 실제로는 1000 이상으로 바꾸세요
            prompt = f"""
Generate a sample conversation turn for a chatbot training dataset.
- age_group: {person['age_group']}
- gender: {person['gender']}
- emotion: {emotion}
- role: {person['role']}
- topic: {person['topic']}
Always answer ONLY in Korean, in JSON format with keys: age_group, gender, emotion, role, content.
Do not add any explanation or English translation.
"""
            print(f"\n[Person: {person['name']}, Emotion: {emotion}, Sample: {i+1}]\nPrompt: {prompt.strip()}\nResponse:")

            stream = ollama.chat(
                model='gemma2:9bp',
                messages=[
                    {'role': 'system', 'content': 'You are a data generator for an empathetic chatbot. Always answer ONLY in Korean, in JSON format.'},
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
                dialogue = json.loads(full_response)
                dialogue['emotion'] = emotion  # 감정 정보 추가
                dialogues.append(dialogue)
            except Exception as e:
                dialogues.append({"error": f"parsing failed: {str(e)}", "raw": full_response})

        result[person['name']][emotion] = dialogues

# JSON 파일로 저장
with open('emotion_chatbot_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n파일이 생성되었습니다: emotion_chatbot_dataset.json")
