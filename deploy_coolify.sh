#!/bin/bash
# Скрипт для автоматического деплоя через Coolify API
# Использование: ./deploy_coolify.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Автоматический деплой через Coolify ===${NC}"
echo ""

# Проверка переменных окружения
if [ -z "$COOLIFY_API_URL" ] || [ -z "$COOLIFY_API_TOKEN" ] || [ -z "$COOLIFY_APPLICATION_UUID" ]; then
    echo -e "${YELLOW}Переменные окружения не установлены.${NC}"
    echo ""
    echo "Установите следующие переменные:"
    echo "  export COOLIFY_API_URL='http://localhost:8000/api/v1'"
    echo "  export COOLIFY_API_TOKEN='your-api-token'"
    echo "  export COOLIFY_APPLICATION_UUID='uksoc0wgw08gk848s4kokg8c'"
    echo ""
    echo "Или создайте файл .env.coolify с этими переменными"
    echo ""
    
    # Попытка загрузить из .env.coolify
    if [ -f .env.coolify ]; then
        echo -e "${YELLOW}Загружаю переменные из .env.coolify...${NC}"
        export $(cat .env.coolify | grep -v '^#' | xargs)
    else
        echo -e "${RED}Ошибка: Переменные окружения не установлены${NC}"
        exit 1
    fi
fi

# Получение последнего коммита из GitHub
echo -e "${YELLOW}Получение последнего коммита из GitHub...${NC}"
cd /root/medkit_fix 2>/dev/null || cd ~/medkit_fix 2>/dev/null || {
    echo -e "${RED}Ошибка: Не найдена директория medkit_fix${NC}"
    exit 1
}

git pull origin main
LATEST_COMMIT=$(git log --oneline -1 | awk '{print $1}')
echo -e "${GREEN}Последний commit: $LATEST_COMMIT${NC}"

# Обновление SOURCE_COMMIT в .env файле Coolify
COOLIFY_APP_DIR="/data/coolify/applications/${COOLIFY_APPLICATION_UUID}"
if [ -d "$COOLIFY_APP_DIR" ]; then
    echo -e "${YELLOW}Обновление SOURCE_COMMIT в Coolify...${NC}"
    cd "$COOLIFY_APP_DIR"
    
    # Обновляем SOURCE_COMMIT
    if [ -f .env ]; then
        sed -i "s/SOURCE_COMMIT=.*/SOURCE_COMMIT=$LATEST_COMMIT/" .env
        echo -e "${GREEN}SOURCE_COMMIT обновлен: $LATEST_COMMIT${NC}"
    else
        echo -e "${YELLOW}Файл .env не найден, создаю...${NC}"
        echo "SOURCE_COMMIT=$LATEST_COMMIT" > .env
    fi
else
    echo -e "${RED}Ошибка: Директория Coolify не найдена: $COOLIFY_APP_DIR${NC}"
    exit 1
fi

# Вариант 1: Использование Coolify API для запуска деплоя
if [ -n "$COOLIFY_API_URL" ] && [ -n "$COOLIFY_API_TOKEN" ]; then
    echo -e "${YELLOW}Запуск деплоя через Coolify API...${NC}"
    
    RESPONSE=$(curl -s -X POST \
        "${COOLIFY_API_URL}/applications/${COOLIFY_APPLICATION_UUID}/deploy" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"commit\":\"${LATEST_COMMIT}\"}" \
        -w "\n%{http_code}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
        echo -e "${GREEN}Деплой запущен успешно!${NC}"
        echo "$BODY"
    else
        echo -e "${RED}Ошибка при запуске деплоя (HTTP $HTTP_CODE)${NC}"
        echo "$BODY"
        exit 1
    fi
else
    # Вариант 2: Использование Coolify UI через docker compose
    echo -e "${YELLOW}Запуск деплоя через docker compose...${NC}"
    cd "$COOLIFY_APP_DIR"
    
    # Останавливаем текущий контейнер
    echo -e "${YELLOW}Остановка текущего контейнера...${NC}"
    docker compose down || true
    
    # Удаляем старый образ
    OLD_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "${COOLIFY_APPLICATION_UUID}" | head -1)
    if [ -n "$OLD_IMAGE" ]; then
        echo -e "${YELLOW}Удаление старого образа: $OLD_IMAGE${NC}"
        docker rmi "$OLD_IMAGE" 2>/dev/null || echo "Образ уже удален"
    fi
    
    # Запускаем деплой через Coolify (нужно использовать правильный способ)
    echo -e "${YELLOW}Для полного деплоя используйте Coolify UI или webhook${NC}"
    echo -e "${YELLOW}Или выполните вручную:${NC}"
    echo "  cd $COOLIFY_APP_DIR"
    echo "  docker compose up -d --build"
fi

echo ""
echo -e "${GREEN}=== Деплой завершен ===${NC}"
echo ""
echo "Проверьте статус в Coolify UI:"
echo "  http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Или проверьте логи:"
echo "  cd $COOLIFY_APP_DIR"
echo "  docker compose logs -f"
