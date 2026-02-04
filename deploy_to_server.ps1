# Скрипт для деплоя приложения на сервер через Coolify
# Использование: .\deploy_to_server.ps1

Write-Host "🚀 Начинаем деплой на сервер..." -ForegroundColor Green

# Проверка наличия git
try {
    $gitVersion = &"C:\Program Files\Git\bin\git.exe" --version
    Write-Host "✓ Git найден: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git не найден! Установите Git." -ForegroundColor Red
    exit 1
}

# Переход в директорию проекта
$projectPath = "D:\ivantuz\profi"
Set-Location $projectPath
Write-Host "📁 Рабочая директория: $projectPath" -ForegroundColor Cyan

# Проверка статуса Git
Write-Host "📋 Проверка изменений..." -ForegroundColor Yellow
$status = &"C:\Program Files\Git\bin\git.exe" status --short

if ($status) {
    Write-Host "📝 Найдены изменения:" -ForegroundColor Cyan
    Write-Host $status
    
    # Добавление всех изменений
    Write-Host "📦 Добавление файлов в Git..." -ForegroundColor Yellow
    &"C:\Program Files\Git\bin\git.exe" add .
    
    # Создание коммита
    $commitMessage = "Deploy: обновление приложения"
    Write-Host "💾 Создание коммита..." -ForegroundColor Yellow
    &"C:\Program Files\Git\bin\git.exe" commit -m $commitMessage
    
    # Push в репозиторий
    Write-Host "⬆ Отправка изменений на GitHub..." -ForegroundColor Yellow
    &"C:\Program Files\Git\bin\git.exe" push origin main
    
    Write-Host "✅ Изменения отправлены на GitHub" -ForegroundColor Green
    Write-Host "🔄 Coolify автоматически задеплоит изменения из ветки main" -ForegroundColor Cyan
} else {
    Write-Host "✓ Нет изменений для коммита" -ForegroundColor Green
    Write-Host "ℹ Все файлы уже синхронизированы с GitHub" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Репозиторий: https://github.com/imuzolev/medkit" -ForegroundColor Cyan
Write-Host "🌐 Coolify UI: http://2.56.240.119:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 Готово! Проверьте статус деплоя в Coolify UI" -ForegroundColor Green
