# Tailscale 공식 이미지 사용 (안정성 확보)
FROM tailscale/tailscale:latest

# Caddy 설치 (Alpine 기반이므로 apk 사용)
RUN apk update && apk add --no-cache caddy socat bind-tools curl
# 스크립트 및 설정 복사
COPY start.sh /start.sh
COPY Caddyfile /etc/caddy/Caddyfile

COPY authkey.txt /root/authkey.txt
# 실행 권한
RUN chmod +x /start.sh

CMD ["/start.sh"]
