from openai import OpenAI
import base64

# Cloud Run 주소 (본인 주소 확인!)
BASE_URL = "https://home-gateway-106839487214.asia-northeast3.run.app/v1"
API_KEY = "EMPTY" 

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# 1. 헬스 체크 (모델 목록 조회)
print("📡 서버 연결 확인 중...")
models = client.models.list()
print(f"✅ 연결 성공! 활성화된 모델: {models.data[0].id}")

# 2. 추론 요청
print("🤖 Qwen2.5-VL에게 질문하는 중...")
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-7B-Instruct",
    messages=[
        {"role": "user", "content": "경희대학교의 최신 소식을 알려줘"}
    ],
    max_tokens=500
)

print(f"🧠 응답: {response.choices[0].message.content}")