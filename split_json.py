import json

# 원본 JSON 파일 경로
input_file = 'emotion_test_data.json'

# 각 카테고리별로 저장할 파일명
output_files = {
    "청소년 여성 학교생활": "teenager_female_school.json",
    "성인 남성 직장생활": "adult_male_work.json",
    "노년층 남성 일상": "senior_male_daily.json"
}

# JSON 파일 읽기
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 각 카테고리별 데이터 추출 및 저장
for category, filename in output_files.items():
    if category in data:
        category_data = data[category]
        with open(filename, 'w', encoding='utf-8') as f_out:
            json.dump(category_data, f_out, ensure_ascii=False, indent=4)
        print(f"{category} 데이터를 {filename} 파일로 저장했습니다.")
    else:
        print(f"{category} 키가 JSON 데이터에 없습니다.")