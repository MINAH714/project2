import ollama
import json
import random

def clean_json_response(raw):
    raw = raw.strip()
    if raw.startswith("``````"):
        return raw[3:-3].strip()
    return raw

# 6가지 감정 리스트
emotions_all = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]

# 각 사람별로 30개의 감정을 랜덤하게 뽑음
persons = [
    {
        "name": "청소년 여성 학교생활",
        "age_group": "청소년",
        "gender": "여성",
        "role": "학생",
        "topic": "학교생활",
        "emotions": [random.choice(emotions_all) for _ in range(100)]
    },
    {
        "name": "성인 남성 직장생활",
        "age_group": "성인",
        "gender": "남성",
        "role": "직장인",
        "topic": "직장생활",
        "emotions": [random.choice(emotions_all) for _ in range(100)]
    },
    {
        "name": "노년층 남성 일상",
        "age_group": "노년층",
        "gender": "남성",
        "role": "일상인",
        "topic": "일상",
        "emotions": [random.choice(emotions_all) for _ in range(100)]
    }
]

result = {}

for person in persons:
    name = person["name"]
    dialogues = []

    for idx, emotion in enumerate(person["emotions"]):
        prompt = f"""
다음 조건에 맞는 챗봇 대화 데이터를 한 개 생성하세요.
- 연령대: {person['age_group']}
- 성별: {person['gender']}
- 상황: {person['topic']}
- 역할: {person['role']}
- 감정: {emotion}
아래 JSON 포맷으로, 코드블록, 마크다운, 설명 없이 순수 JSON만 출력하세요.
반드시 emotion 필드는 위 감정({emotion})으로 출력하세요.
예시:
{{"age_group":"{person['age_group']}","gender":"{person['gender']}","role":"{person['role']}","situation":"{person['topic']}","emotion":"{emotion}","content":"여기에 대화 내용을 작성하세요."}}
"""
        print(f"\n[Person: {name}, Emotion: {emotion}, Sample: {idx+1}]\nPrompt: {prompt.strip()}\nResponse:")

        stream = ollama.chat(
            model='gemma2:9b',
            messages=[
                {'role': 'system', 'content': 'You are a data generator for an empathetic chatbot. Always answer ONLY in Korean, in JSON format.'},
                {'role': 'user', 'content': prompt}
            ],
            stream=True
        )

        full_response = ''
        for chunk in stream:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            full_response += content
        print("\n---")

        cleaned = clean_json_response(full_response)
        try:
            dialogue = json.loads(cleaned)
            dialogues.append(dialogue)
        except Exception as e:
            dialogues.append({"error": f"parsing failed: {str(e)}", "raw": cleaned})

    result[name] = dialogues

# 최종 결과를 JSON 파일로 저장
with open('emotion_test_random_data1.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n파일이 생성되었습니다: emotion_test_random_data1.json")
