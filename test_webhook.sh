#!/bin/bash
# Скрипт для проверки webhook Coolify

WEBHOOK_URL="http://2.56.240.119:8888/webhooks/source/github/events/uksoc0wgw08gk848s4kokg8c"

echo "=== Тестирование webhook ==="
echo "URL: $WEBHOOK_URL"
echo ""

# Тестовый payload от GitHub (push event)
PAYLOAD='{
  "ref": "refs/heads/main",
  "before": "0000000000000000000000000000000000000000",
  "after": "3f6e18d1234567890abcdef1234567890abcdef",
  "repository": {
    "id": 1148454109,
    "name": "medkit",
    "full_name": "imuzolev/medkit"
  },
  "pusher": {
    "name": "test",
    "email": "test@example.com"
  }
}'

echo "Отправка POST запроса..."
echo ""

# Отправка запроса
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: test-delivery-id" \
  -d "$PAYLOAD" \
  -v

echo ""
echo ""
echo "=== Проверка завершена ==="
echo ""
echo "Ожидаемые результаты:"
echo "- 200 OK = webhook работает"
echo "- 302 = редирект (требуется авторизация)"
echo "- 401/403 = требуется авторизация"
echo "- 404 = webhook не найден"
