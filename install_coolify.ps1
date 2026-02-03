# Скрипт для установки Coolify на сервер
# Использование: .\install_coolify.ps1

$SERVER = "root@2.56.240.119"
$SCRIPT_NAME = "setup_coolify.sh"

Write-Host "🚀 Установка Coolify на сервер..." -ForegroundColor Green
Write-Host ""

# Проверка наличия скрипта
if (-not (Test-Path $SCRIPT_NAME)) {
    Write-Host "❌ Ошибка: Файл $SCRIPT_NAME не найден!" -ForegroundColor Red
    exit 1
}

Write-Host "📤 Загрузка скрипта на сервер..." -ForegroundColor Yellow
scp $SCRIPT_NAME "${SERVER}:/tmp/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при загрузке скрипта" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Скрипт загружен" -ForegroundColor Green
Write-Host ""

Write-Host "🔧 Выполнение установки на сервере..." -ForegroundColor Yellow
Write-Host "⚠️  Это может занять несколько минут..." -ForegroundColor Yellow
Write-Host ""

# Выполнение скрипта на сервере
ssh $SERVER "chmod +x /tmp/$SCRIPT_NAME && /tmp/$SCRIPT_NAME"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Coolify успешно установлен!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Следующие шаги:" -ForegroundColor Cyan
    Write-Host "1. Откройте в браузере: http://2.56.240.119:8000" -ForegroundColor White
    Write-Host "2. Создайте административный аккаунт" -ForegroundColor White
    Write-Host "3. Создайте новый проект" -ForegroundColor White
    Write-Host "4. Подключите GitHub репозиторий: imuzolev/medkit" -ForegroundColor White
    Write-Host "5. Настройте автоматический деплой" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 Подробная инструкция: см. COOLIFY_SETUP.md" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Ошибка при установке Coolify" -ForegroundColor Red
    Write-Host "Проверьте логи выше для деталей" -ForegroundColor Yellow
    exit 1
}
