#!/bin/bash
# Скрипт для проверки порта приложения

echo "=== Проверка порта приложения ==="
echo ""

# Проверка процесса python app.py
echo "Процесс python app.py:"
ps aux | grep "python app.py" | grep -v grep
echo ""

# Проверка портов
echo "Проверка портов:"
netstat -tulpn | grep python
echo ""

# Или через ss
echo "Проверка через ss:"
ss -tulpn | grep python
echo ""

# Проверка порта 3000
echo "Проверка порта 3000:"
netstat -tulpn | grep 3000
ss -tulpn | grep 3000
echo ""

# Проверка переменных окружения процесса
echo "Переменные окружения процесса:"
PID=$(ps aux | grep "python app.py" | grep -v grep | awk '{print $2}' | head -1)
if [ ! -z "$PID" ]; then
    echo "PID процесса: $PID"
    cat /proc/$PID/environ | tr '\0' '\n' | grep PORT
else
    echo "Процесс не найден"
fi
