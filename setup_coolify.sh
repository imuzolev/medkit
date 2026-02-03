#!/bin/bash
# Скрипт для установки Coolify на сервер
# Использование: ./setup_coolify.sh

set -e

echo "🚀 Начинаем установку Coolify на сервер..."
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Скрипт должен быть запущен от имени root${NC}"
    exit 1
fi

# Шаг 1: Проверка и установка Docker
echo -e "${YELLOW}Шаг 1: Проверка Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker не найден. Устанавливаем Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}✓ Docker установлен${NC}"
else
    echo -e "${GREEN}✓ Docker уже установлен: $(docker --version)${NC}"
fi

# Шаг 2: Проверка Docker Compose
echo -e "${YELLOW}Шаг 2: Проверка Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose не найден. Устанавливаем..."
    # Для новых версий Docker Compose встроен
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✓ Docker Compose доступен через 'docker compose'${NC}"
    else
        # Установка старой версии docker-compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}✓ Docker Compose установлен${NC}"
    fi
else
    echo -e "${GREEN}✓ Docker Compose уже установлен${NC}"
fi

# Шаг 3: Создание директории для Coolify
echo -e "${YELLOW}Шаг 3: Создание директории для Coolify...${NC}"
COOLIFY_DIR="/data/coolify"
mkdir -p $COOLIFY_DIR
cd $COOLIFY_DIR
echo -e "${GREEN}✓ Директория создана: $COOLIFY_DIR${NC}"

# Шаг 4: Скачивание docker-compose.yml для Coolify
echo -e "${YELLOW}Шаг 4: Скачивание конфигурации Coolify...${NC}"
if [ ! -f "docker-compose.yml" ]; then
    curl -o docker-compose.yml https://cdn.coollabs.io/coolify/docker-compose.yml
    echo -e "${GREEN}✓ Конфигурация скачана${NC}"
else
    echo -e "${GREEN}✓ Конфигурация уже существует${NC}"
fi

# Шаг 5: Запуск Coolify
echo -e "${YELLOW}Шаг 5: Запуск Coolify...${NC}"
if docker compose ps | grep -q coolify; then
    echo "Coolify уже запущен. Перезапускаем..."
    docker compose down
fi

docker compose up -d

echo ""
echo -e "${GREEN}✓ Coolify установлен и запущен!${NC}"
echo ""
echo "📋 Следующие шаги:"
echo "1. Откройте в браузере: http://$(hostname -I | awk '{print $1}'):8000"
echo "   (или http://2.56.240.119:8000)"
echo "2. Создайте административный аккаунт"
echo "3. Создайте новый проект"
echo "4. Подключите GitHub репозиторий: imuzolev/medkit"
echo "5. Настройте автоматический деплой"
echo ""
echo "📚 Документация: https://coolify.io/docs"
echo ""
echo -e "${GREEN}Готово!${NC}"
