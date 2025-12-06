# Hybrid Cloud AI Server (RTX 3090 + GCP)

> **Low-Cost, Unlimited AI API Server powered by Home GPU**  
> 로컬 GPU(RTX 3090)를 GCP Cloud Run과 Tailscale로 연결하여, 전 세계 어디서든 접속 가능한 API 서버로 구축했습니다.

## 1. Overview

이 프로젝트는 **1인 기업의 AI 서비스 운영**를 위한 비용 효율적인 하이브리드 클라우드 아키텍처입니다.
고비용의 클라우드 GPU 인스턴스 대신 **로컬 GPU(On-Premise)**를 활용하며, **Cloud Run**을 게이트웨이로 사용하여 보안과 접근성을 동시에 해결했습니다.

*   **Cost Efficiency:** 유휴 상태 시 비용 $0 (Serverless). GPU 연산 비용 0원 (전기세 제외).
*   **Performance:** vLLM 엔진을 통한 SOTA급 Vision Model (Qwen2.5-VL) 서빙.
*   **Security:** 포트포워딩 없는 **Zero-Trust** VPN 터널링 (Tailscale).
*   **Usability:** Streamlit 기반의 웹 클라이언트로 손쉽게 테스트 및 데모 가능.

---

## 2. Architecture & Data Flow

### 🔄 Data Flow Summary
> **"웹 클라이언트가 질문을 던지면, 구글 클라우드(Gateway)가 이를 받아서 비밀 터널(Tailscale)로 집 안의 RTX 3090에게 전달하고, GPU가 생각한 결과를 다시 역순으로 가져오는 구조입니다."**

**`사용자(Web Client)`** ➡ **`Cloud Run (Gateway)`** ➡ **`Tailscale (VPN)`** ➡ **`집 서버 (RTX 3090)`** ➡ **`vLLM (AI)`**

### 🏗 System Diagram

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffcc00', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#f4f4f4'}}}%%
graph TD
    %% 스타일 정의
    classDef client fill:#FF9F43,stroke:#333,stroke-width:2px,color:white,rx:10,ry:10;
    classDef gcp fill:#4285F4,stroke:#333,stroke-width:2px,color:white,rx:5,ry:5;
    classDef home fill:#2E86AB,stroke:#333,stroke-width:2px,color:white,rx:5,ry:5;
    classDef k8s fill:#326CE5,stroke:#333,stroke-width:2px,color:white,rx:5,ry:5;
    classDef gpu fill:#76B900,stroke:#333,stroke-width:4px,color:white,rx:5,ry:5,stroke-dasharray: 5 5;

    %% 노드 정의
    subgraph Client["💻 Local Environment"]
        WebClient["🖥️ Web Client Container<br>(Streamlit)"]:::client
    end
    
    subgraph Cloud["☁️ Google Cloud Platform"]
        CloudRun["🚀 Cloud Run Gateway<br>(Caddy + Tailscale)"]:::gcp
    end

    subgraph Home["🏠 Home Network (On-Premise)"]
        HomeNIC["🔌 Server NIC<br>(Tailscale Interface)"]:::home
        
        subgraph Cluster["☸️ K3s Kubernetes Cluster"]
            Ingress["🚪 Ingress<br>(Traefik Controller)"]:::k8s
            Service["🔀 vLLM Service"]:::k8s
            Pod["🧠 vLLM Pod<br>(Qwen2.5-VL)"]:::k8s
        end
        
        GPU["⚡ NVIDIA RTX 3090<br>(Time-Slicing: 1/10)"]:::gpu
    end

    %% 연결
    WebClient ==>|HTTPS Request (JSON)| CloudRun
    CloudRun ==>|Secure VPN Tunnel| HomeNIC
    HomeNIC -->|Port 80| Ingress
    Ingress -->|Routing| Service
    Service -->|Select Pod| Pod
    Pod -.->|CUDA Ops| GPU
```

---

## 3. Component Roles

| Component | Container Name | Role | Data Exchange |
| :--- | :--- | :--- | :--- |
| **Web Client** | `rtx3090-web-client` | **사용자 인터페이스 (UI)** | **송신:** 텍스트/이미지(Base64) JSON 요청<br>**수신:** AI 응답 스트리밍 |
| **Gateway** | `home-gateway` | **보안 터널 입구 (GCP)** | **입력:** HTTPS 요청<br>**처리:** Caddy → Tailscale VPN 중계<br>**출력:** 집 서버 응답 반환 |
| **AI Inference** | `vLLM Pod` | **실제 두뇌 (GPU 연산)** | **입력:** OpenAI API 포맷 요청<br>**처리:** Qwen2.5-VL 모델 추론<br>**출력:** 텍스트 토큰 생성 |

---

## 4. Tech Stack

| Category | Technology | Reason for Selection |
| :--- | :--- | :--- |
| **Frontend** | **Streamlit** | Python만으로 빠르게 대화형 AI 웹 인터페이스 구축 가능. |
| **Gateway** | **GCP Cloud Run** | 완전 관리형 서버리스. 유휴 시 비용이 0원이며, 고정 IP 없이도 안정적인 HTTPS 엔드포인트 제공. |
| **Network** | **Tailscale** | 복잡한 방화벽/포트포워딩 설정 없이 NAT를 관통하는 Mesh VPN. 보안성이 뛰어남. |
| **Proxy** | **Caddy** | 설정이 간편하고 HTTPS 및 Reverse Proxy 처리가 뛰어난 경량 웹 서버. |
| **Orchestration** | **K3s** | 단일 노드 GPU 서버에 최적화된 경량 Kubernetes. 리소스 오버헤드 최소화. |
| **Inference** | **vLLM** | **Continuous Batching** 기술로 Ollama 대비 압도적인 처리량(Throughput) 제공. OpenAI API 규격 호환. |
| **Model** | **Qwen2.5-VL** | 이미지 내 좌표(Bounding Box) 인식 능력이 탁월하여 로보틱스 VLA 작업에 최적. |

---

## 5. Usage Guide (Command Cheat Sheet)

### A. 웹 클라이언트 실행 (Web Client)
Streamlit 기반의 웹 인터페이스로, 텍스트/이미지를 입력하고 실시간 로그를 확인할 수 있습니다.

```bash
# 1. 클라이언트 폴더로 이동
cd ~/Projects/personal-cloud-hub/client-web

# 2. Docker 이미지 빌드 (이름: rtx3090-web-client)
docker build -t rtx3090-web-client .

# 3. 컨테이너 실행
# 웹 브라우저에서 http://localhost:8501 접속
docker run -p 8501:8501 rtx3090-web-client
```

### B. GCP Cloud Run 관리 (Gateway)
이 프로젝트 루트 폴더(`~/Projects/personal-cloud-hub`)에서 실행합니다.

```bash
# 1. 이미지 빌드
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/home-gateway .

# 2. 서비스 배포 (Tailscale Auth Key 필수)
gcloud run deploy home-gateway \
  --image gcr.io/$(gcloud config get-value project)/home-gateway \
  --set-env-vars TAILSCALE_AUTH_KEY="[YOUR-REUSABLE-KEY]" \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080
```

### C. 로컬 서버(집) 전원 관리
집에 있는 물리 서버(RTX 3090)를 끄거나 켤 때의 절차입니다.

#### 1. 시스템 종료 (Shutdown)
```bash
# 1. K3s 서비스 정지
sudo systemctl stop k3s

# 2. 시스템 종료
sudo shutdown -h now
```

#### 2. 시스템 부팅 후 확인 (Startup)
```bash
# 1. Tailscale 연결 확인 (IP가 100.x.y.z 대역인지 확인)
tailscale status
tailscale ip -4

# 2. K3s 및 GPU 상태 점검
sudo systemctl status k3s
kubectl describe node | grep "nvidia.com/gpu"
# -> 결과가 "nvidia.com/gpu: 10" (Time Slicing 적용됨) 이어야 함
```

---

## 6. Troubleshooting Journey (Deep Dive)

이 프로젝트를 구축하며 겪었던 주요 기술적 난관과 해결 과정을 공유합니다.

### 1. 동적 IP 환경에서의 K3s 무한 재부팅 (CrashLoopBackOff)
*   **문제:** 가정용 인터넷(DHCP) 특성상 재부팅 시 서버 IP가 변경됨.
*   **해결:** 부팅 시 현재 IP를 감지하여 `systemd` 서비스 파일을 동적으로 수정하고, 꼬인 TLS 인증서를 초기화하는 **Start-up Script** 작성.

### 2. Cloud Run과 Tailscale 인증 키 충돌
*   **문제:** Cloud Run 배포 시 `invalid key` 오류 발생.
*   **해결:** `Reusable` & `Ephemeral` 옵션이 켜진 Tailscale Auth Key를 사용하고, 공백 없이 환경변수로 주입.

### 3. 이미지 전송 시 502 Bad Gateway & Timeout
*   **문제:** 고화질 이미지 전송 시 60초 후 타임아웃 발생.
*   **해결:**
    1.  Tailscale MTU를 1280으로 설정.
    2.  Cloud Run 타임아웃을 300초로 확장.
    3.  **Client-side Optimization:** 이미지를 1024px로 리사이징하여 전송.

### 4. Docker 이미지 혼동 (Tailscale Login Loop)
*   **문제:** 웹 클라이언트 실행 시 Tailscale 로그인 창이 뜨며 무한 대기.
*   **원인:** 게이트웨이용 이미지(`home-gateway`)와 클라이언트용 이미지(`web-client`)가 같은 태그로 빌드되어 덮어씌워짐.
*   **해결:** 클라이언트 이미지를 `rtx3090-web-client`로 명확히 구분하여 빌드.

## 7. Health Check Commands (Cheat Sheet)

시스템의 각 구성 요소가 정상적으로 작동하는지 확인하기 위한 필수 명령어 모음입니다.

### A. Docker Containers (Client & Gateway)

```bash
# 1. 실행 중인 모든 컨테이너 확인
docker ps

# 2. 특정 컨테이너 로그 확인 (실시간)
# 웹 클라이언트 로그
docker logs -f $(docker ps -qf "ancestor=rtx3090-web-client")

# 3. 컨테이너 리소스 사용량 확인 (CPU/Memory)
docker stats
```

### B. Kubernetes & GPU (Home Server)

```bash
# 1. K3s 클러스터 노드 상태 확인 (Ready 상태여야 함)
kubectl get nodes

# 2. GPU 인식 상태 확인 (nvidia.com/gpu: 10 확인)
kubectl describe node | grep "nvidia.com/gpu"

# 3. 모든 Pod 상태 확인 (Running 상태여야 함)
kubectl get pods -A

# 4. vLLM (AI 모델) 로그 확인
# 'vllm'이 포함된 Pod의 로그를 실시간으로 조회
kubectl logs -f -l app=vllm-qwen

# 5. Ingress (Traefik) 상태 확인
kubectl get ingress -A
```

### C. Network & VPN (Tailscale)

```bash
# 1. Tailscale 연결 상태 및 내 IP 확인
tailscale status
tailscale ip -4

# 2. Tailscale 피어(Peer) 간 연결 테스트 (Cloud Run -> Home Server)
tailscale ping 100.x.y.z
```
