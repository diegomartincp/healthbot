# HealthBot

Bot de Telegram que permite monitorizar varios dominios para ver si funcionan correctamente, notificando cuando no lo hacen

## Getting started

Ejemplo de ejecución en local:

docker run -e HEALTH_CHECK_DOMAINS="https://www.google.com" \
 -e TELEGRAM_TOKEN="7829620002:AAE0b3HetwNk1D9G885Pt46vMVZnvj3Uhwk" \
 -e TELEGRAM_CHAT_ID="1080451655" \
 diegomartinc/healthbot:proxy

Ejecutar con DOCKER COMPOSE:
docker-compose up -d
