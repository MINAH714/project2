import ollama
import json

# 프롬프트 (영어, JSON 출력 강제)
prompt = """
You are an assistant for generating emotional dialogue scenarios.
Please generate over 100 short Q&A dialogue pairs for a teenage girl persona who feels sad.
Each pair should be a short user utterance and a chatbot response that shows empathy.
"""

response = ollama.chat(
    model='gemma3:latest',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant for generating emotional dialogue scenarios. Always output in JSON as specified.'},
        {'role': 'user', 'content': prompt}
    ]
)

try:
    # 응답에서 순수 JSON 추출 (필요시 파싱)
    result = response['message']['content']
    result = json.loads(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print('❌ Error while parsing response:', e)
    print('Original response:', response['message']['content'])
