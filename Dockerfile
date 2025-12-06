FROM tailscale/tailscale:latest

RUN apk update && apk add --no-cache caddy socat bind-tools curl
COPY start.sh /start.sh
COPY Caddyfile /etc/caddy/Caddyfile
COPY authkey.txt /root/authkey.txt
RUN chmod +x /start.sh

CMD ["/start.sh"]
