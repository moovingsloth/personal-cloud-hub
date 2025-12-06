from openai import OpenAI
import base64

BASE_URL = "https://home-gateway-106839487214.asia-northeast3.run.app/v1"
API_KEY = "EMPTY" 

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# 1x1 픽셀 검은 점 (용량 극소)
TINY_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="

try:
    print("🔬 초소형 이미지 테스트 중...")
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-7B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 사진의 색깔이 뭐야?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{TINY_IMAGE}"}},
                ],
            }
        ],
        max_tokens=100,
    )
    print(f"✅ 성공! 응답: {response.choices[0].message.content}")

except Exception as e:
    print(f"❌ 실패: {e}")