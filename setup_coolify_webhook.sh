#!/bin/bash
# Скрипт для настройки автоматического деплоя из GitHub в Coolify
# Использование: ./setup_coolify_webhook.sh

set -e

echo "=== Настройка автоматического деплоя Coolify + GitHub ==="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия необходимых переменных
if [ -z "$COOLIFY_APP_ID" ]; then
    echo -e "${YELLOW}Переменная COOLIFY_APP_ID не установлена${NC}"
    echo "Найдите ID приложения в Coolify UI или в пути: /data/coolify/applications/<APP_ID>"
    read -p "Введите APP_ID приложения: " COOLIFY_APP_ID
fi

APP_DIR="/data/coolify/applications/$COOLIFY_APP_ID"

if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}Ошибка: Директория приложения не найдена: $APP_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Найдена директория приложения: $APP_DIR${NC}"
echo ""

# Переход в директорию приложения
cd "$APP_DIR"

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}Ошибка: Файл .env не найден${NC}"
    exit 1
fi

echo "=== Текущая конфигурация ==="
echo "SOURCE_COMMIT: $(grep SOURCE_COMMIT .env | cut -d= -f2 || echo 'не установлен')"
echo ""

# Получение последнего коммита из GitHub репозитория
echo "=== Получение последнего коммита из GitHub ==="
read -p "Введите путь к локальному клону репозитория (например, /root/medkit_fix): " REPO_PATH

if [ ! -d "$REPO_PATH" ]; then
    echo -e "${RED}Ошибка: Директория репозитория не найдена: $REPO_PATH${NC}"
    exit 1
fi

cd "$REPO_PATH"

# Проверка, что это git репозиторий
if [ ! -d ".git" ]; then
    echo -e "${RED}Ошибка: Это не git репозиторий${NC}"
    exit 1
fi

# Получение последнего коммита
echo "Обновление репозитория..."
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "Предупреждение: не удалось обновить репозиторий"

LATEST_COMMIT=$(git log --oneline -1 | awk '{print $1}')
echo -e "${GREEN}Последний commit: $LATEST_COMMIT${NC}"

# Обновление SOURCE_COMMIT в .env
cd "$APP_DIR"
echo ""
echo "=== Обновление конфигурации Coolify ==="
sed -i "s/SOURCE_COMMIT=.*/SOURCE_COMMIT=$LATEST_COMMIT/" .env
echo -e "${GREEN}SOURCE_COMMIT обновлен до: $LATEST_COMMIT${NC}"

# Проверка обновления
echo ""
echo "=== Проверка обновления ==="
cat .env | grep SOURCE_COMMIT

echo ""
echo -e "${YELLOW}=== Важно: Автоматический деплой через webhook ==="
echo -e "${NC}Для автоматического деплоя при каждом push в GitHub:"
echo ""
echo "1. Откройте Coolify UI: http://$(hostname -I | awk '{print $1}'):8000"
echo "2. Перейдите в настройки вашего приложения"
echo "3. Найдите раздел 'Webhooks' или 'Git Integration'"
echo "4. Скопируйте URL webhook"
echo "5. В GitHub перейдите: Settings → Webhooks → Add webhook"
echo "6. Вставьте URL webhook от Coolify"
echo "7. Content type: application/json"
echo "8. Events: Just the push event"
echo ""
echo -e "${GREEN}После настройки webhook, каждый push в main ветку будет автоматически деплоиться${NC}"
echo ""

# Опция ручного деплоя через Coolify UI
echo -e "${YELLOW}=== Ручной деплой (если webhook не настроен) ==="
echo -e "${NC}Вы можете запустить деплой вручную через Coolify UI:"
echo "1. Откройте приложение в Coolify"
echo "2. Нажмите кнопку 'Deploy' или 'Redeploy'"
echo ""

# Опция перезапуска через docker compose
read -p "Перезапустить приложение сейчас? (y/n): " RESTART_NOW

if [ "$RESTART_NOW" = "y" ] || [ "$RESTART_NOW" = "Y" ]; then
    echo ""
    echo "=== Остановка текущего контейнера ==="
    docker compose down 2>/dev/null || echo "Контейнер уже остановлен"
    
    echo ""
    echo "=== Запуск через Coolify ==="
    echo -e "${YELLOW}Внимание: Для правильной сборки используйте Coolify UI${NC}"
    echo "Coolify автоматически соберет образ при следующем деплое"
    echo ""
    echo "Или запустите вручную через Coolify UI:"
    echo "1. Откройте приложение"
    echo "2. Нажмите 'Deploy'"
    echo ""
fi

echo -e "${GREEN}=== Настройка завершена! ===${NC}"
echo ""
echo "Проверьте статус приложения в Coolify UI"
