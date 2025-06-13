import ollama
import json
import random

def generate_prompt(person, main_emotion, sub_emotions, ratios, count):
    prompt = f"""
다음 조건에 맞는 챗봇 대화 데이터를 {count}개 생성하세요.
- 연령대: {person['age_group']}
- 성별: {person['gender']}
- 상황: {person['topic']}
- 주 감정: {main_emotion} ({int(ratios[0]*100)}%)
- 보조 감정1: {sub_emotions[0]} ({int(ratios[1]*100)}%)
- 보조 감정2: {sub_emotions[1]} ({int(ratios[2]*100)}%)
대화는 사람이 실제로 대화하는 것처럼 감정이 자연스럽게 변해야 합니다.
각 대화는 아래 JSON 포맷으로 출력하세요.
{{"age_group":"{person['age_group']}","gender":"{person['gender']}","main_emotion":"{main_emotion}","sub_emotions":{{"{sub_emotions[0]}":{ratios[1]}, "{sub_emotions[1]}":{ratios[2]}}},"role":"{person['role']}","situation":"{person['topic']}","emotion":"[감정]","content":"[대화내용]"}}
(코드블록, 마크다운, 설명 없이 JSON만 출력)
"""
    return prompt

# 예시 사용
persons = [
    {"name": "청소년 여성 학교생활", "age_group": "청소년", "gender": "여성", "role": "학생", "topic": "학교생활"},
    {"name": "성인 남성 직장생활", "age_group": "성인", "gender": "남성", "role": "직장인", "topic": "직장생활"},
    {"name": "노년층 남성 일상", "age_group": "노년층", "gender": "남성", "role": "일상인", "topic": "일상"}
]
main_emotions = ["슬픔", "분노", "기쁨"]
sub_emotions_list = [["놀람", "기쁨"], ["슬픔", "혐오"], ["두려움", "슬픔"]]
ratios_list = [[0.6, 0.1, 0.3], [0.6, 0.1, 0.3], [0.6, 0.1, 0.3]]

for i, person in enumerate(persons):
    prompt = generate_prompt(person, main_emotions[i], sub_emotions_list[i], ratios_list[i], 10)
    # ollama API 호출 및 결과 저장(실제 구현 필요)
    print(prompt)
