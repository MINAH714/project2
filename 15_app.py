import ollama
import json
import random
from datetime import datetime, timedelta

def clean_json_response(raw):
    raw = raw.strip()
    # 백틱 3개로 감싸져 있으면 제거
    if raw.startswith("``````"):
        return raw[3:-3].strip()
    return raw

# 6 emotions in English
emotions_all = ["Joy", "Anger", "Sadness", "Fear", "Surprise", "Disgust"]

# Date range: 2025-06-09 (Mon) ~ 2025-06-15 (Sun)
start_date = datetime(2025, 6, 9)
end_date = datetime(2025, 6, 15)

def generate_random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

persons = [
    {
        "name": "Adolescent Male Daily Life",
        "age_group": "Adolescent",
        "gender": "Male",
        "role": "High School Student",
        "topic": "Daily Life",
        "emotions": [random.choice(emotions_all) for _ in range(2)]
    },
    {
        "name": "Adult Female Daily Life",
        "age_group": "Adult",
        "gender": "Female",
        "role": "Housewife",
        "topic": "Daily Life",
        "emotions": [random.choice(emotions_all) for _ in range(2)]
    },
    {
        "name": "Elderly Male Daily Life",
        "age_group": "Elderly",
        "gender": "Male",
        "role": "Retiree",
        "topic": "Daily Life",
        "emotions": [random.choice(emotions_all) for _ in range(2)]
    }
]

result = {}

for person in persons:
    name = person["name"]
    dialogues = []

    for idx, emotion in enumerate(person["emotions"]):
        random_date = generate_random_date(start_date, end_date)
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
            dialogue['date'] = random_date  # Add random date
            dialogues.append(dialogue)
        except Exception as e:
            dialogues.append({"error": f"parsing failed: {str(e)}", "raw": cleaned, "date": random_date})

    result[name] = dialogues

# Save to JSON file
with open('emotion_test_random_data2.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n파일이 생성되었습니다: emotion_test_random_data2.json")
