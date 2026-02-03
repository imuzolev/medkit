# Скрипт для обновления проекта на сервере Beget
# Установка кодировки UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$SERVER = "root@2.56.240.119"
$REMOTE_PATH = "~/analiz_aptechki"

Write-Host "=== Обновление проекта на сервере Beget ===" -ForegroundColor Green
Write-Host ""

# Проверка наличия необходимых файлов
$requiredFiles = @("app.py", "requirements.txt", "templates", "static")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "Ошибка: Отсутствуют необходимые файлы:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Шаг 1: Остановка приложения на сервере..." -ForegroundColor Yellow
ssh $SERVER "sudo systemctl stop analiz_aptechki 2>/dev/null || true"
ssh $SERVER "pkill -f 'python.*app.py' 2>/dev/null || true"

Write-Host "Шаг 2: Создание бэкапа на сервере..." -ForegroundColor Yellow
ssh $SERVER "cd ~ && cp -r $REMOTE_PATH ${REMOTE_PATH}_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"

Write-Host "Шаг 3: Загрузка обновленных файлов..." -ForegroundColor Yellow
scp app.py "${SERVER}:${REMOTE_PATH}/"
scp requirements.txt "${SERVER}:${REMOTE_PATH}/"
scp -r templates "${SERVER}:${REMOTE_PATH}/"
scp -r static "${SERVER}:${REMOTE_PATH}/"

Write-Host "Шаг 4: Обновление зависимостей..." -ForegroundColor Yellow
$cmd1 = 'cd ~/analiz_aptechki; source venv/bin/activate; pip install --upgrade pip'
$cmd2 = 'cd ~/analiz_aptechki; source venv/bin/activate; pip install -r requirements.txt'
ssh $SERVER $cmd1
ssh $SERVER $cmd2

Write-Host "Шаг 5: Запуск приложения..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Выберите способ запуска:" -ForegroundColor Cyan
Write-Host "1. Через systemd (sudo systemctl start analiz_aptechki)" -ForegroundColor White
Write-Host "2. Вручную в фоне (nohup python app.py > app.log 2>&1 &)" -ForegroundColor White
Write-Host "3. Пропустить (запустите вручную позже)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Введите номер (1-3)"

switch ($choice) {
    "1" {
        ssh $SERVER "sudo systemctl start analiz_aptechki"
        Write-Host "Приложение запущено через systemd" -ForegroundColor Green
    }
    "2" {
        $startCmd = 'cd ~/analiz_aptechki; source venv/bin/activate; nohup python app.py > app.log 2>&1 &'
        ssh $SERVER $startCmd
        Write-Host "Приложение запущено в фоне" -ForegroundColor Green
    }
    "3" {
        Write-Host "Запуск пропущен" -ForegroundColor Yellow
    }
    default {
        Write-Host "Неверный выбор, запуск пропущен" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Обновление завершено! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Проверьте статус приложения:" -ForegroundColor Cyan
Write-Host "  ssh $SERVER 'cd $REMOTE_PATH && tail -f app.log'" -ForegroundColor White
