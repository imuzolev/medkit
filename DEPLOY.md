# Инструкция по деплою и обновлению проекта

## Первоначальная установка на сервере Beget

### 1. Подключение к серверу

```bash
ssh root@2.56.240.119
```

Введите пароль при запросе.

### 2. Создание директории проекта

```bash
# Перейдите в домашнюю директорию
cd ~

# Создайте директорию для проекта
mkdir -p analiz_aptechki
cd analiz_aptechki
```

### 3. Создание файла analiz_aptechki в корне

```bash
# Вернитесь в корень
cd ~

# Создайте файл analiz_aptechki
touch analiz_aptechki
echo "Проект анализа аптечки" > analiz_aptechki
```

### 4. Загрузка файлов проекта

На вашем локальном компьютере выполните:

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

Или вручную через SCP:
```bash
scp -r app.py requirements.txt templates/ static/ root@2.56.240.119:~/analiz_aptechki/
```

### 5. Настройка на сервере

После загрузки файлов на сервере выполните:

```bash
cd ~/analiz_aptechki

# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Настройка запуска приложения

На Beget обычно используется systemd или supervisor. Создайте файл для запуска:

```bash
# Создайте файл запуска
nano ~/analiz_aptechki/start.sh
```

Содержимое `start.sh`:
```bash
#!/bin/bash
cd ~/analiz_aptechki
source venv/bin/activate
python app.py
```

Сделайте файл исполняемым:
```bash
chmod +x ~/analiz_aptechki/start.sh
```

### 7. Настройка systemd (опционально)

Если у вас есть права root, создайте systemd service:

```bash
sudo nano /etc/systemd/system/analiz_aptechki.service
```

Содержимое:
```ini
[Unit]
Description=Analiz Aptechki Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/root/analiz_aptechki
Environment="PATH=/root/analiz_aptechki/venv/bin"
ExecStart=/root/analiz_aptechki/venv/bin/python /root/analiz_aptechki/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable analiz_aptechki
sudo systemctl start analiz_aptechki
```

Проверка статуса:
```bash
sudo systemctl status analiz_aptechki
```

---

## Обновление проекта

### Быстрое обновление (через скрипт)

На вашем локальном компьютере:

**Windows (PowerShell):**
```powershell
.\update.ps1
```

### Ручное обновление

#### 1. Подключитесь к серверу

```bash
ssh root@2.56.240.119
```

#### 2. Остановите приложение (если запущено)

Если используется systemd:
```bash
sudo systemctl stop analiz_aptechki
```

Или найдите процесс и остановите:
```bash
ps aux | grep app.py
kill <PID>
```

#### 3. Перейдите в директорию проекта

```bash
cd ~/analiz_aptechki
```

#### 4. Загрузите обновленные файлы

На локальном компьютере выполните:

```bash
# Загрузка обновленных файлов
scp app.py root@2.56.240.119:~/analiz_aptechki/
scp -r templates/ root@2.56.240.119:~/analiz_aptechki/
scp -r static/ root@2.56.240.119:~/analiz_aptechki/

# Если изменились зависимости
scp requirements.txt root@2.56.240.119:~/analiz_aptechki/
```

#### 5. Обновите зависимости (если нужно)

На сервере:
```bash
cd ~/analiz_aptechki
source venv/bin/activate
pip install -r requirements.txt
```

#### 6. Запустите приложение

Если используется systemd:
```bash
sudo systemctl start analiz_aptechki
```

Или вручную:
```bash
cd ~/analiz_aptechki
source venv/bin/activate
python app.py
```

Для запуска в фоне:
```bash
nohup python app.py > app.log 2>&1 &
```

---

## Проверка работы приложения

### Проверка логов

Если используется systemd:
```bash
sudo journalctl -u analiz_aptechki -f
```

Или проверьте файл логов:
```bash
tail -f ~/analiz_aptechki/app.log
```

### Проверка порта

```bash
netstat -tulpn | grep 5000
# или
ss -tulpn | grep 5000
```

### Тестирование

Откройте в браузере:
- `http://2.56.240.119:5000` (если порт открыт)
- Или используйте домен, настроенный в панели Beget

---

## Важные замечания

1. **Порт**: На Beget может потребоваться настроить порт через панель управления или использовать переменные окружения.

2. **Firewall**: Убедитесь, что порт 5000 открыт в настройках Beget.

3. **Python версия**: Убедитесь, что на сервере установлен Python 3.7 или выше:
   ```bash
   python3 --version
   ```

4. **Зависимости**: OpenCV требует дополнительных системных библиотек. Если возникнут проблемы, установите:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-opencv libopencv-dev
   ```

5. **Права доступа**: Убедитесь, что у пользователя есть права на запись в директорию проекта.

---

## Откат к предыдущей версии

Если что-то пошло не так:

1. Остановите приложение
2. Восстановите предыдущие файлы из бэкапа
3. Перезапустите приложение

Рекомендуется делать бэкап перед каждым обновлением:
```bash
cp -r ~/analiz_aptechki ~/analiz_aptechki_backup_$(date +%Y%m%d)
```
