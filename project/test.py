import ollama
import random
import json
import re

model = "gemma2:9b"
prompt = (
    "You are a data generator for an empathetic chatbot. "
    "Generate realistic Korean-language conversations between virtual characters. "
    "Always answer ONLY in Korean, in JSON format with keys: age_group, gender, emotion, role, content. "
    "Do not add any explanation or English translation."
)

response_stream = ollama.generate(
    model=model,
    prompt=prompt,
    stream=True
)

buffer = ""
for chunk in response_stream:
    buffer += chunk['response']

# JSON 배열에서 각 대화문만 추출
try:
    # 줄바꿈, 공백 정리
    buffer = buffer.replace('\n', '').replace('\r', '')
    # JSON 파싱
    dialogues = json.loads(buffer)
    if isinstance(dialogues, list) and dialogues:
        # 한 줄씩 출력
        for dialogue in dialogues:
            print(dialogue.strip())
    else:
        print("생성된 대화문이 없습니다.")
except Exception as e:
    print(f"에러 발생: {e}")
    # 비정상 출력일 경우, 따옴표로 감싸진 문자열만 추출해서 출력
    lines = re.findall(r'"(.*?)"', buffer, re.DOTALL)
    if lines:
        for line in lines:
            print(line.strip())
    else:
        print("생성된 대화문이 없습니다.")
