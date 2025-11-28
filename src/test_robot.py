from openai import OpenAI
import base64
import io
import os
from PIL import Image

# 1. Cloud Run 주소
BASE_URL = "https://home-gateway-106839487214.asia-northeast3.run.app/v1"
API_KEY = "EMPTY" 

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# 2. 이미지 파일 (테스트용)
IMAGE_PATH = "test.jpg" # 원본 고화질 사진도 OK

# 3. [핵심] 스마트 리사이징 함수
def encode_image_optimized(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ '{image_path}' 파일이 없습니다.")

    with Image.open(image_path) as img:
        # (1) RGB 변환 (PNG 투명도 호환성 문제 방지)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # (2) 리사이징: 긴 변을 1024px로 맞춤 (비율 유지)
        # Qwen-VL은 1024px 정도면 충분히 작은 글씨도 다 읽습니다.
        max_size = 1024
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))

        # (3) JPEG 압축: 품질 85% (용량을 1/10로 줄여줌)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        
        # 디버깅용: 용량 확인
        size_kb = buffer.tell() / 1024
        print(f"📉 이미지 최적화 완료: {size_kb:.2f} KB로 전송")
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

try:
    print(f"📸 '{IMAGE_PATH}' 처리 중...")
    image_data = encode_image_optimized(IMAGE_PATH)

    print("🚀 RTX 3090(Qwen2.5-VL)에게 분석 요청...")
    
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-7B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ],
            }
        ],
        max_tokens=500,
        stream=True # 스트리밍으로 응답 즉시 확인
    )

    print("\n🧠 [RTX 3090 응답]:")
    print("----------------------------------------")
    
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
            
    print("\n----------------------------------------")
    print("✅ 완료!")

except Exception as e:
    print(f"\n❌ 오류 발생: {e}")