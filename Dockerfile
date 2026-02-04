# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p templates static

# Открываем порт (Coolify использует PORT из переменной окружения, обычно 3000)
# Экспонируем оба порта для совместимости
EXPOSE 3000 5000

# Запускаем приложение
CMD ["python", "app.py"]
