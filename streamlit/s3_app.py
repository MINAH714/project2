import streamlit as st
import boto3
import os
import uuid
from dotenv import load_dotenv # .env 파일 로드를 위한 라이브러리

# .env 파일에서 환경 변수 로드
load_dotenv()

def upload_file_to_s3(uploaded_file_content, bucket_name, object_name):
    """
    파일 내용을 S3 버킷에 업로드합니다.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_REGION")
    )
    
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=uploaded_file_content)
        return True
    except Exception as e:
        st.error(f"S3 업로드 오류 발생: {e}")
        return False

# --- Streamlit 앱 시작 ---
st.set_page_config(layout="centered", page_title="S3 다중 파일 업로더")

st.title("☁️ S3 다중 파일 업로더")

st.markdown("""
이 앱은 **여러 파일**을 한 번에 업로드하고 AWS S3 버킷에 저장할 수 있도록 돕습니다.
각 파일에 대해 S3에 저장될 이름을 직접 지정할 수 있으며, 지정된 **'저장 경로 (Prefix)'** 안에 파일이 저장됩니다.
**AWS 자격 증명(Access Key, Secret Key, Region)**은 앱과 **같은 경로 내의 `.env` 파일**에서 로드됩니다.
""")

# 1. 파일 업로드 섹션
st.header("1. 파일 선택")
uploaded_files = st.file_uploader("여기에 파일들을 드래그하거나 클릭하여 업로드하세요.", type=None, accept_multiple_files=True) 

# 2. S3 설정 입력 섹션
st.header("2. S3 버킷 정보 입력")

default_bucket = os.environ.get("S3_BUCKET_NAME", "")
default_region = os.environ.get("AWS_REGION", "ap-southeast-2") # 서울 리전 기본값

s3_bucket_name = st.text_input("S3 버킷 이름", value=default_bucket, 
                                help="파일을 저장할 S3 버킷의 이름을 입력하세요.")

# 사용자가 저장 경로(Prefix)를 입력하도록 추가
s3_save_prefix = st.text_input("S3 저장 경로 (예: folder/subfolder/ 또는 dummy/)", value="dummy/",
                               help="S3 버킷 내에 파일을 저장할 가상 폴더 경로를 지정합니다. 마지막에 '/'를 포함해야 합니다.")
# 사용자가 입력한 Prefix의 마지막이 '/'가 아니면 추가
if s3_save_prefix and not s3_save_prefix.endswith('/'):
    s3_save_prefix += '/'


# 3. 각 파일의 S3 저장 이름 지정 섹션
file_names_to_save = {}
if uploaded_files:
    st.subheader("4. 각 파일의 S3 저장 이름 지정")
    for i, file in enumerate(uploaded_files):
        original_filename_no_ext, file_extension = os.path.splitext(file.name)
        # S3_SAVE_PREFIX를 적용한 제안 이름
        suggested_name = f"{original_filename_no_ext}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        file_names_to_save[file.name] = st.text_input(
            f"'{file.name}'을(를) S3에 저장할 이름:", 
            value=suggested_name, # 여기서 Prefix는 제외하고 순수 파일 이름만 제안
            key=f"filename_input_{i}", 
            help=f"S3 버킷 내의 지정된 경로 ('{s3_save_prefix}')에 '{file.name}'이(가) 저장될 파일 이름을 입력하세요."
        )
else:
    st.info("파일을 먼저 업로드해야 S3에 저장될 파일 이름을 설정할 수 있습니다.")


# 5. 업로드 버튼
st.header("5. S3에 업로드")

if st.button("🚀 선택된 파일 모두 S3에 업로드"):
    if not uploaded_files:
        st.warning("먼저 업로드할 파일들을 선택해주세요.")
    elif not s3_bucket_name:
        st.warning("S3 버킷 이름을 입력해주세요.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_files = len(uploaded_files)
        uploaded_count = 0
        
        for idx, file in enumerate(uploaded_files):
            user_defined_filename = file_names_to_save.get(file.name)

            if not user_defined_filename:
                st.error(f"❌ 파일 '{file.name}'에 대한 S3 저장 이름을 입력하지 않았습니다. 이 파일을 건너뜁니다.")
                progress_bar.progress((idx + 1) / total_files)
                continue

            # 최종 S3 객체 키 생성: Prefix + 사용자가 입력한 파일 이름
            final_s3_object_key = f"{s3_save_prefix}{user_defined_filename}"

            status_text.text(f"[{idx + 1}/{total_files}] '{file.name}' -> '{final_s3_object_key}' 업로드 중...")
            
            file_content = file.read()
            if upload_file_to_s3(file_content, s3_bucket_name, final_s3_object_key):
                uploaded_count += 1
                st.success(f"✅ 파일 '{file.name}'이(가) S3에 '{final_s3_object_key}' 이름으로 성공적으로 업로드되었습니다!")
                file_url = f"https://{s3_bucket_name}.s3.{os.environ.get('AWS_REGION', default_region)}.amazonaws.com/{final_s3_object_key}"
                st.info(f"업로드된 파일 URL: [클릭]({file_url})")
            else:
                st.error(f"❌ 파일 '{file.name}' ('{final_s3_object_key}') 업로드에 실패했습니다. AWS 자격 증명 또는 버킷 권한을 확인해주세요.")
            
            progress_bar.progress((idx + 1) / total_files)

        status_text.text("업로드 완료!")
        st.success(f"총 {uploaded_count}개의 파일이 성공적으로 업로드되었습니다.")
        if uploaded_count == total_files:
            st.balloons() 

st.markdown("---")
st.caption("개발자: Gemini AI")