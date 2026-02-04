#!/bin/bash
# Скрипт для проверки приложения внутри контейнера

CONTAINER_ID=$(docker ps | grep uksoc0wgw08gk848s4kokg8c | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "Контейнер не найден"
    exit 1
fi

echo "=== Проверка приложения в контейнере ==="
echo "Container ID: $CONTAINER_ID"
echo ""

# Проверка порта внутри контейнера
echo "1. Проверка порта 3000 внутри контейнера:"
docker exec $CONTAINER_ID netstat -tulpn | grep 3000
docker exec $CONTAINER_ID ss -tulpn | grep 3000
echo ""

# Проверка процесса
echo "2. Проверка процесса Python:"
docker exec $CONTAINER_ID ps aux | grep python
echo ""

# Тест подключения внутри контейнера
echo "3. Тест подключения к приложению (внутри контейнера):"
docker exec $CONTAINER_ID curl -s http://localhost:3000/ | head -20
echo ""

# Полные логи
echo "4. Полные логи контейнера:"
docker logs $CONTAINER_ID | tail -50
echo ""

# Проверка переменных окружения
echo "5. Переменные окружения контейнера:"
docker exec $CONTAINER_ID env | grep PORT
echo ""
