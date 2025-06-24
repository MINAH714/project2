import ollama
import json
import random  
from datetime import datetime, timedelta

def clean_json_response(raw):
    raw = raw.strip()
    if raw.startswith("``````"):
        return raw[3:-3].strip()
    return raw

# 6가지 감정 리스트
emotions_all = ["기쁨", "분노", "슬픔", "두려움", "놀람", "혐오"]

# 날짜 범위 설정
start_date = datetime(2025, 6, 9)  # 6월 9일 월요일
end_date = datetime(2025, 6, 15)   # 6월 15일 일요일

def generate_random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

persons = [
    {
        "name": "청소년 여성 일상생활",
        "age_group": "청소년",
        "gender": "여성",
        "role": "고등학생",
        "topic": "일상생활",
        "emotions": [random.choice(emotions_all) for _ in range(250)]
    },
    {
        "name": "성인 남성 일상생활",
        "age_group": "성인",
        "gender": "남성",
        "role": "직장인",
        "topic": "일상생활",
        "emotions": [random.choice(emotions_all) for _ in range(250)]
    },
    {
        "name": "노년층 남성 일상생활",
        "age_group": "노년층",
        "gender": "남성",
        "role": "은퇴자",
        "topic": "일상생활",
        "emotions": [random.choice(emotions_all) for _ in range(250)]
    }
]

result = {}

for person in persons:
    name = person["name"]
    dialogues = []

    for idx, emotion in enumerate(person["emotions"]):
        random_date = generate_random_date(start_date, end_date).strftime('%Y-%m-%d')
        prompt = f"""
Generate a single chatbot conversation data with the following conditions.
- Age group: {person['age_group']}
- Gender: {person['gender']}
- Situation: {person['topic']}
- Role: {person['role']}
- Emotion: {emotion}
Respond ONLY in Korean. Output ONLY valid JSON (no code blocks, no markdown, no explanation).
Make sure the emotion field matches the above emotion ({emotion}).
Example:
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
            dialogue['date'] = random_date  # 랜덤 날짜 추가
            dialogues.append(dialogue)
        except Exception as e:
            dialogues.append({"error": f"parsing failed: {str(e)}", "raw": cleaned})

    result[name] = dialogues

# JSON 파일로 저장
with open('emotion_test_random_data4.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n파일이 생성되었습니다: emotion_test_random_data4.json")
