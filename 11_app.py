import ollama
import json
import random

def clean_json_response(raw):
    raw = raw.strip()
    # 백틱 3개로 감싸져 있으면 제거
    if raw.startswith("``````"):
        return raw[3:-3].strip()
    return raw

# 감정별 개수를 직접 지정
persons = [
    {
        "name": "청소년 여성 학교생활",
        "age_group": "청소년",
        "gender": "여성",
        "role": "학생",
        "topic": "학교생활",
        "emotions": [("슬픔", 18), ("놀람", 3), ("기쁨", 9)]  # 총 30개
    },
    {
        "name": "성인 남성 직장생활",
        "age_group": "성인",
        "gender": "남성",
        "role": "직장인",
        "topic": "직장생활",
        "emotions": [("분노", 18), ("슬픔", 3), ("혐오", 9)]  # 예시
    },
    {
        "name": "노년층 남성 일상",
        "age_group": "노년층",
        "gender": "남성",
        "role": "일상인",
        "topic": "일상",
        "emotions": [("기쁨", 18), ("두려움", 3), ("슬픔", 9)]  # 예시
    }
]

result = {}

for person in persons:
    name = person["name"]

    # 감정 분포 리스트 생성 (개수만큼 emotion을 넣음)
    emotions_list = []
    for emo, num in person["emotions"]:
        emotions_list += [emo] * num
    random.shuffle(emotions_list)

    dialogues = []

    for idx, emotion in enumerate(emotions_list):
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

        # Ollama에 프롬프트 전송, 스트리밍으로 응답 받음
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
            print(content, end='', flush=True)  # 실시간 출력
            full_response += content
        print("\n---")

        cleaned = clean_json_response(full_response)
        try:
            dialogue = json.loads(cleaned)
            dialogues.append(dialogue)
        except Exception as e:
            dialogues.append({"error": f"parsing failed: {str(e)}", "raw": cleaned})

# 최종 결과를 JSON 파일로 저장
with open('emotion_test_random_data', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n파일이 생성되었습니다: emotion_test_random_data.json")
