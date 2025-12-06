import streamlit as st
from openai import OpenAI
import base64
import io
from PIL import Image
import os

# 페이지 설정
st.set_page_config(page_title="RTX 3090 AI Client", page_icon="🤖", layout="wide")

st.title("🤖 RTX 3090 AI Client (Web)")
st.markdown("Cloud Run Gateway를 통해 집 안의 **RTX 3090 (Qwen2.5-VL)** 와 통신합니다.")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    # [핵심 변경] 쿠버네티스 내부 서비스 DNS를 기본값으로 사용
    default_url = os.getenv("API_BASE_URL", "http://vllm-service:80/v1")
    base_url = st.text_input("API Base URL", value=default_url)
    api_key = st.text_input("API Key", value="EMPTY", type="password")
    model_name = st.text_input("Model Name", value="Qwen/Qwen2.5-VL-7B-Instruct")

    st.divider()

# 이미지 최적화 함수
def encode_image_optimized(image_file):
    with Image.open(image_file) as img:
        # (1) RGB 변환
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # (2) 리사이징
        max_size = 1024
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))

        # (3) JPEG 압축
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        
        size_kb = buffer.tell() / 1024
        return base64.b64encode(buffer.getvalue()).decode('utf-8'), size_kb

# 메인 UI
st.subheader("🚀 클라이언트 모드 선택")
mode = st.radio("모드 선택", ["기본 테스트 (Simple Test)", "고급 대화 (Advanced Chat)"], horizontal=True)

if mode == "기본 테스트 (Simple Test)":
    st.info("1x1 픽셀 이미지를 전송하여 연결을 테스트합니다.")
    
    if st.button("테스트 실행 (Run Test)", type="primary"):
        client = OpenAI(base_url=base_url, api_key=api_key)
        
        # 1x1 픽셀 검은 점
        TINY_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        
        try:
            with st.spinner("🔬 초소형 이미지 테스트 중..."):
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "이 사진의 색깔이 뭐야?"},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{TINY_IMAGE}"}},
                            ],
                        }
                    ],
                    max_tokens=15,
                )
            st.success(f"✅ 성공! 응답: {response.choices[0].message.content}")
            
            with st.expander("상세 로그"):
                st.json(response.model_dump())
                
        except Exception as e:
            st.error(f"❌ 실패: {e}")

else:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. 입력 (Input)")
        uploaded_file = st.file_uploader("이미지를 업로드하세요 (선택)", type=["jpg", "jpeg", "png"])
        use_sample = st.checkbox("테스트용 샘플 이미지 사용 (1x1 Pixel)", value=False)
        user_prompt = st.text_area("질문 입력", value="이 이미지에서 '물체'를 식별하고 그 좌표(bounding box)를 JSON으로 알려줘.", height=150)
        
        send_btn = st.button("🚀 전송 (Send)", type="primary")

    with col2:
        st.subheader("2. 결과 (Output)")
        output_container = st.empty()
        log_expander = st.expander("📜 처리 로그 (Logs)", expanded=True)

    if send_btn:
        if not user_prompt:
            st.warning("질문을 입력해주세요.")
        else:
            client = OpenAI(base_url=base_url, api_key=api_key)
            
            messages = []
            content_list = [{"type": "text", "text": user_prompt}]
            
            try:
                with log_expander:
                    st.write("🔄 연결 초기화 중...")
                    
                    image_payload = None
                    if uploaded_file:
                        st.write(f"📸 이미지 처리 중... ({uploaded_file.name})")
                        image_data, size_kb = encode_image_optimized(uploaded_file)
                        st.write(f"📉 이미지 최적화 완료: {size_kb:.2f} KB로 전송")
                        image_payload = {"url": f"data:image/jpeg;base64,{image_data}"}
                    elif use_sample:
                        st.write("🧪 샘플 이미지(1x1 Pixel) 사용")
                        TINY_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
                        image_payload = {"url": f"data:image/png;base64,{TINY_IMAGE}"}
                    else:
                        st.warning("⚠️ 이미지가 선택되지 않았습니다. 텍스트만 전송됩니다.")

                    if image_payload:
                        content_list.append({
                            "type": "image_url", 
                            "image_url": image_payload
                        })
                    
                    messages.append({
                        "role": "user",
                        "content": content_list
                    })
                    
                    st.write("🚀 RTX 3090에게 요청 전송...")
                    
                    response_stream = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=1024,
                        stream=True
                    )
                    
                    st.write("✅ 응답 수신 시작!")

                # 스트리밍 응답 표시
                full_response = ""
                for chunk in response_stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        output_container.markdown(full_response + "▌")
                
                output_container.markdown(full_response)
                
                with log_expander:
                    st.write("✅ 완료!")

            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
                with log_expander:
                    st.write(f"Error details: {e}")
