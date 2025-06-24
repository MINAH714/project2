import streamlit as st
import json
import boto3
import os

# AWS S3 설정 (환경 변수 또는 ~/.aws/credentials에서 자동으로 로드)
# 명시적으로 설정하려면 아래 주석 해제 후 YOUR_BUCKET_NAME을 실제 버킷 이름으로 변경
# S3_BUCKET_NAME = "your-s3-bucket-name"

def merge_json_files(uploaded_files):
    """
    업로드된 JSON 파일들을 병합합니다.
    각 JSON 파일이 루트에 리스트를 포함한다고 가정합니다.
    """
    merged_data = []
    for file in uploaded_files:
        try:
            # Streamlit UploadedFile 객체는 BytesIO와 유사하므로 직접 로드 가능
            data = json.load(file)
            if isinstance(data, list):
                merged_data.extend(data)
            else:
                st.warning(f"경고: 파일 '{file.name}'은(는) 루트에 리스트를 포함하지 않으므로 건너뜝니다.")
        except json.JSONDecodeError:
            st.error(f"오류: 파일 '{file.name}'은(는) 유효한 JSON 형식이 아닙니다.")
        except Exception as e:
            st.error(f"파일 '{file.name}' 처리 중 오류 발생: {e}")
    return merged_data

def upload_to_s3(file_content, bucket_name, object_name):
    """
    파일 내용을 S3 버킷에 업로드합니다.
    """
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=file_content)
        return True
    except Exception as e:
        st.error(f"S3 업로드 오류: {e}")
        return False

st.title("JSON 파일 병합 및 관리 도구")

st.markdown("""
이 도구는 여러 JSON 파일을 병합하고, 병합된 데이터를 다운로드하거나
AWS S3 버킷에 업로드할 수 있도록 돕습니다.
""")

# 1. 파일 업로드 섹션
st.header("1. JSON 파일 업로드")
uploaded_files = st.file_uploader("JSON 파일을 선택하세요", type="json", accept_multiple_files=True)

merged_json_string = None
if uploaded_files:
    st.success(f"{len(uploaded_files)}개의 파일이 업로드되었습니다.")
    
    # 파일 병합
    merged_data = merge_json_files(uploaded_files)

    if merged_data:
        st.header("2. 병합된 JSON 데이터")
        merged_json_string = json.dumps(merged_data, indent=2, ensure_ascii=False)
        st.json(merged_data) # Streamlit의 st.json은 예쁘게 출력해줍니다.

        # 3. 다운로드 버튼
        st.header("3. 병합된 파일 다운로드")
        st.download_button(
            label="병합된 JSON 다운로드",
            data=merged_json_string.encode('utf-8'), # 바이트로 인코딩
            file_name="merged_output.json",
            mime="application/json"
        )
    else:
        st.warning("병합할 유효한 JSON 데이터가 없습니다.")

# 4. S3 업로드 섹션
if merged_json_string:
    st.header("4. AWS S3에 업로드")
    s3_bucket_name = st.text_input("S3 버킷 이름", value=os.environ.get("S3_BUCKET_NAME", ""))
    s3_object_key = st.text_input("S3 객체 키 (파일명)", value="merged_output.json")

    if st.button("S3에 업로드"):
        if s3_bucket_name and s3_object_key:
            with st.spinner("S3에 업로드 중..."):
                if upload_to_s3(merged_json_string.encode('utf-8'), s3_bucket_name, s3_object_key):
                    st.success(f"'{s3_object_key}' 파일이 '{s3_bucket_name}' 버킷에 성공적으로 업로드되었습니다!")
                else:
                    st.error("S3 업로드에 실패했습니다. AWS 자격 증명 및 버킷 이름/권한을 확인해주세요.")
        else:
            st.warning("S3 버킷 이름과 객체 키를 입력해주세요.")
else:
    st.info("먼저 JSON 파일을 업로드하여 병합된 데이터를 생성해주세요.")

st.markdown("---")
st.markdown("개발자: Gemini AI")