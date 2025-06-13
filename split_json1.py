import json

# data4 파일 읽기
with open('emotion_test_random_data4.json', encoding='utf-8') as f:
    data4 = json.load(f)

# 각 카테고리별로 분리
adolescent_female = data4.get("청소년 여성 일상생활", [])
adult_male = data4.get("성인 남성 일상생활", [])
elderly_male = data4.get("노년층 남성 일상생활", [])

# 각각 파일로 저장
with open('adolescent_female_daily.json', 'w', encoding='utf-8') as f:
    json.dump(adolescent_female, f, ensure_ascii=False, indent=2)

with open('adult_male_daily.json', 'w', encoding='utf-8') as f:
    json.dump(adult_male, f, ensure_ascii=False, indent=2)

with open('elderly_male_daily.json', 'w', encoding='utf-8') as f:
    json.dump(elderly_male, f, ensure_ascii=False, indent=2)