# HealthBot 
HealthBot lets you supervise the accessibility of your websites (or any public domains) and sends real-time alerts via Telegram as soon as a problem is detected. No more worrying about downtime going unnoticed: receive critical notifications right on your favorite messenger!

## 💡 Features
- Multi-domain monitoring: Supervise several domains at once.
- Telegram notifications: Get instant alerts if any domain is down.
- Easy setup with Docker: Run HealthBot as a lightweight Docker container or via Docker Compose.
- Environment variable configuration: Set monitored domains, bot token, and chat target in seconds.

## Getting Started
### 🛠️ Requirements
- Docker or Docker Compose installed.
- A Telegram Bot Token from @BotFather.
- Your Telegram chat ID (can be obtained with @userinfobot).

### 🖥️ Quickstart with Docker

``` shell
docker run \
  -e HEALTH_CHECK_DOMAINS="https://www.google.com" \
  -e TELEGRAM_TOKEN="<your_bot_token>" \
  -e TELEGRAM_CHAT_ID="<your_chat_id>" \
  diegomartinc/healthbot:proxy`
```

Or with Docker Compose:

``` shell
docker-compose up -d
```

The bot will regularly check the specified domains and send a Telegram message if any become unreachable.

## ⚙️ Configuration
Set the following environment variables:
- HEALTH_CHECK_DOMAINS — Comma-separated list of domains to monitor (https://domain1.com,https://domain2.com)
- TELEGRAM_TOKEN — Token from @BotFather
- TELEGRAM_CHAT_ID — Your Telegram chat ID (use @userinfobot to find yours)

## 🤔 How it works
HealthBot periodically checks the availability (HTTP status) of each configured domain.

If a domain returns an error or is unreachable, an alert message is sent to the configured Telegram chat.

When the domain becomes healthy again, it notifies you of the recovery.

## Why use HealthBot?
- Easily monitor client sites, personal projects, or your business infrastructure from a single Telegram chat.
- Stay informed of outages before your users notice.
- Simple yet extensible: suitable for personal and small business use cases.
