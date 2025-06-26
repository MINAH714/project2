import streamlit as st
import boto3
import os
import uuid
from dotenv import load_dotenv # .env 파일 로드를 위한 라이브러리

# .env 파일에서 환경 변수 로드
load_dotenv()

# S3 파일 업로드 함수 정의
def upload_file_to_s3(file_content, bucket_name, object_name, region_name):
    """
    파일 내용을 지정된 S3 버킷의 객체 이름으로 업로드합니다.
    Args:
        file_content: 업로드할 파일의 바이너리 내용.
        bucket_name (str): 파일을 업로드할 S3 버킷의 이름.
        object_name (str): S3에 저장될 파일의 전체 경로 및 이름.
        region_name (str): S3 버킷이 위치한 AWS 리전.
    Returns:
        bool: 업로드 성공 시 True, 실패 시 False.
    """
    try:
        # AWS S3 클라이언트 초기화
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=region_name
        )
        
        # 파일 업로드
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=file_content)
        return True
    except Exception as e:
        # 업로드 실패 시 오류 메시지 출력
        st.error(f"S3 업로드 오류 발생: {e}")
        return False

# Streamlit 앱 페이지 설정
st.set_page_config(layout="wide", page_title="S3 다중 파일 업로더")

# --- 사이드바 메뉴 정의 ---
with st.sidebar:
    st.header("✨ **메뉴**") # 사이드바 메뉴 제목
    st.markdown("---") # 메뉴 구분선

    # 사이드바 렌더링 확인용 테스트 텍스트 (문제 해결 후 삭제 가능)
    # st.write("사이드바가 보이나요?")

    # 사이드바 링크 버튼을 위한 CSS 스타일
    st.markdown("""
    <style>
    .button-link {
        display: block; /* 블록 요소로 만들어 전체 너비를 차지하게 함 */
        text-decoration: none; /* 밑줄 제거 */
        color: white !important; /* 텍스트 색상 (Streamlit 기본 스타일 재정의) */
        background-color: #31333F; /* 버튼 배경색 */
        padding: 10px 20px; /* 버튼 내부 패딩 */
        border-radius: 8px; /* 둥근 모서리 */
        text-align: left; /* 텍스트 왼쪽 정렬 */
        margin-bottom: 10px; /* 버튼 간 간격 */
        font-weight: bold; /* 텍스트 굵게 */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* 은은한 그림자 */
        transition: background-color 0.3s ease; /* 호버 시 부드러운 전환 효과 */
    }
    .button-link:hover {
        background-color: #78B3CE; /* 호버 시 색상 변경 */
    }
    </style>
    """, unsafe_allow_html=True)

    # 각 메뉴 항목 HTML 링크
    st.markdown('<a href="https://quickly-inspired-midge.ngrok-free.app" target="_blank" class="button-link">🔗 Dummy</a>', unsafe_allow_html=True)
    st.markdown('<a href="#" target="_blank" class="button-link">☁️ S3</a>', unsafe_allow_html=True)
    st.markdown('<a href="http://3.107.174.223:8000/test" target="_blank" class="button-link">🤖 Chatbot</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://13.238.128.251:8503" class="button-link">📄 Report</a>', unsafe_allow_html=True)


# --- 메인 앱 콘텐츠 시작 ---
st.title("☁️ S3 다중 파일 업로더")

st.markdown("""
이 앱은 **여러 파일**을 한 번에 업로드하고 AWS S3 버킷에 저장할 수 있도록 돕습니다.
각 파일에 대해 S3에 저장될 이름을 직접 지정할 수 있으며, 지정된 **'저장 경로 (Prefix)'** 안에 파일이 저장됩니다.
**AWS 자격 증명(Access Key, Secret Key, Region)**은 앱과 **같은 경로 내의 `.env` 파일**에서 로드됩니다.
""")

# 1. 파일 업로드 섹션
st.header("1. 파일 선택")
uploaded_files = st.file_uploader(
    "여기에 파일들을 드래그하거나 클릭하여 업로드하세요.", 
    type=None, 
    accept_multiple_files=True
) 

# 2. S3 설정 입력 섹션
st.header("2. S3 버킷 정보 입력")

# .env 파일에서 기본값 로드
default_bucket = os.environ.get("S3_BUCKET_NAME", "")
default_region = os.environ.get("AWS_REGION", "ap-southeast-2") # 서울 리전 기본값

# S3 버킷 이름 입력 필드
s3_bucket_name = st.text_input(
    "S3 버킷 이름", 
    value=default_bucket, 
    help="파일을 저장할 S3 버킷의 이름을 입력하세요."
)

# S3 저장 경로 (Prefix) 입력 필드
s3_save_prefix = st.text_input(
    "S3 저장 경로 (예: folder/subfolder/ 또는 dummy/)", 
    value="dummy/",
    help="S3 버킷 내에 파일을 저장할 가상 폴더 경로를 지정합니다. 마지막에 '/'를 포함해야 합니다."
)

# 사용자가 입력한 Prefix의 마지막이 '/'가 아니면 추가하여 일관성 유지
if s3_save_prefix and not s3_save_prefix.endswith('/'):
    s3_save_prefix += '/'

# 3. 각 파일의 S3 저장 이름 지정 섹션
file_names_to_save = {}
if uploaded_files:
    st.subheader("3. 각 파일의 S3 저장 이름 지정") # 헤더 번호 수정
    for i, file in enumerate(uploaded_files):
        original_filename_no_ext, file_extension = os.path.splitext(file.name)
        # S3에 저장될 고유한 이름 제안 (원본 파일명 + 고유 ID + 확장자)
        suggested_name = f"{original_filename_no_ext}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        file_names_to_save[file.name] = st.text_input(
            f"'{file.name}'을(를) S3에 저장할 이름:", 
            value=suggested_name, # 사용자에게 제안하는 기본 파일 이름
            key=f"filename_input_{i}", # 각 입력 위젯의 고유 키
            help=f"S3 버킷 내의 지정된 경로 ('{s3_save_prefix}')에 '{file.name}'이(가) 저장될 파일 이름을 입력하세요."
        )
else:
    st.info("파일을 먼저 업로드해야 S3에 저장될 파일 이름을 설정할 수 있습니다.")


# 4. 업로드 버튼 섹션
st.header("4. S3에 업로드") # 헤더 번호 수정

if st.button("🚀 선택된 파일 모두 S3에 업로드"):
    # 필수 입력 값 검증
    if not uploaded_files:
        st.warning("먼저 업로드할 파일들을 선택해주세요.")
    elif not s3_bucket_name:
        st.warning("S3 버킷 이름을 입력해주세요.")
    else:
        progress_bar = st.progress(0) # 업로드 진행률 표시
        status_text = st.empty() # 현재 업로드 상태 메시지 표시
        
        total_files = len(uploaded_files)
        uploaded_count = 0
        
        # 각 파일에 대한 업로드 처리
        for idx, file in enumerate(uploaded_files):
            user_defined_filename = file_names_to_save.get(file.name)

            # 사용자가 파일 이름을 지정했는지 확인
            if not user_defined_filename:
                st.error(f"❌ 파일 '{file.name}'에 대한 S3 저장 이름을 입력하지 않았습니다. 이 파일을 건너뜁니다.")
                progress_bar.progress((idx + 1) / total_files) # 진행률 업데이트
                continue

            # 최종 S3 객체 키 생성: 저장 경로 (Prefix) + 사용자가 입력한 파일 이름
            final_s3_object_key = f"{s3_save_prefix}{user_defined_filename}"

            # 현재 업로드 중인 파일 정보 표시
            status_text.text(f"[{idx + 1}/{total_files}] '{file.name}' -> '{final_s3_object_key}' 업로드 중...")
            
            # 파일 내용 읽기
            file_content = file.read()
            
            # S3 업로드 함수 호출
            if upload_file_to_s3(file_content, s3_bucket_name, final_s3_object_key, default_region):
                uploaded_count += 1 # 성공적으로 업로드된 파일 수 증가
                st.success(f"✅ 파일 '{file.name}'이(가) S3에 '{final_s3_object_key}' 이름으로 성공적으로 업로드되었습니다!")
                
                # 업로드된 파일의 공개 URL 생성 및 표시
                file_url = f"https://{s3_bucket_name}.s3.{default_region}.amazonaws.com/{final_s3_object_key}"
                st.info(f"업로드된 파일 URL: [클릭]({file_url})")
            else:
                # 업로드 실패 시 메시지 출력
                st.error(f"❌ 파일 '{file.name}' ('{final_s3_object_key}') 업로드에 실패했습니다. AWS 자격 증명 또는 버킷 권한을 확인해주세요.")
            
            progress_bar.progress((idx + 1) / total_files) # 진행률 업데이트

        status_text.text("업로드 완료!") # 최종 상태 메시지
        st.success(f"총 {uploaded_count}개의 파일이 성공적으로 업로드되었습니다.")
        if uploaded_count == total_files:
            st.balloons() # 모든 파일이 성공적으로 업로드되었을 경우 풍선 효과

# --- 하단 링크 및 개발자 정보 ---
st.link_button("Chatbot", url="http://3.107.174.223:8000/test")

st.markdown("---")
st.caption("개발자: Minah")
