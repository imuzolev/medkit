# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем PyTorch CPU-only (без CUDA — экономим ~1.5 ГБ)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p templates static

# Открываем порт (Coolify использует PORT из переменной окружения, обычно 3000)
# Экспонируем оба порта для совместимости
EXPOSE 3000 5000

# Запускаем приложение через gunicorn для production
# Используем переменную PORT из окружения (Coolify устанавливает её автоматически)
# Если PORT не установлен, используем 5000 по умолчанию
CMD sh -c 'gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 2 --timeout 120 --access-logfile - --error-logfile - app:app'
