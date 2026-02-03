# Скрипт для деплоя проекта на GitHub
# Использование: .\deploy_to_github.ps1

Write-Host "🚀 Начинаем деплой на GitHub..." -ForegroundColor Green

# Проверка наличия git
try {
    $gitVersion = git --version
    Write-Host "✓ Git найден: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git не найден! Установите Git и добавьте его в PATH." -ForegroundColor Red
    Write-Host "Скачать Git: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Переход в директорию проекта
$projectPath = "D:\ivantuz\profi"
Set-Location $projectPath
Write-Host "📁 Рабочая директория: $projectPath" -ForegroundColor Cyan

# Проверка инициализации git
if (-not (Test-Path ".git")) {
    Write-Host "📦 Инициализация git репозитория..." -ForegroundColor Yellow
    git init
} else {
    Write-Host "✓ Git репозиторий уже инициализирован" -ForegroundColor Green
}

# Добавление remote (если еще не добавлен)
$remoteUrl = "https://github.com/imuzolev/medkit.git"
$existingRemote = git remote get-url origin 2>$null

if ($existingRemote) {
    Write-Host "✓ Remote уже настроен: $existingRemote" -ForegroundColor Green
    if ($existingRemote -ne $remoteUrl) {
        Write-Host "⚠ Обновление remote URL..." -ForegroundColor Yellow
        git remote set-url origin $remoteUrl
    }
} else {
    Write-Host "🔗 Добавление remote: $remoteUrl" -ForegroundColor Yellow
    git remote add origin $remoteUrl
}

# Добавление всех файлов
Write-Host "📝 Добавление файлов в git..." -ForegroundColor Yellow
git add .

# Проверка статуса
$status = git status --short
if ($status) {
    Write-Host "📋 Изменения для коммита:" -ForegroundColor Cyan
    Write-Host $status
    
    # Создание коммита
    $commitMessage = "Initial commit: Flask app for medkit analysis"
    Write-Host "💾 Создание коммита..." -ForegroundColor Yellow
    git commit -m $commitMessage
    
    # Push в репозиторий
    Write-Host "⬆ Отправка изменений на GitHub..." -ForegroundColor Yellow
    Write-Host "⚠ Внимание: Если это первый push, может потребоваться авторизация!" -ForegroundColor Yellow
    
    # Попытка push
    try {
        git push -u origin main
        Write-Host "✅ Успешно отправлено в ветку 'main'" -ForegroundColor Green
    } catch {
        # Если ветка main не существует, пробуем master
        try {
            git push -u origin master
            Write-Host "✅ Успешно отправлено в ветку 'master'" -ForegroundColor Green
        } catch {
            Write-Host "⚠ Возможно, нужно создать ветку или настроить авторизацию" -ForegroundColor Yellow
            Write-Host "Выполните вручную: git push -u origin main" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "✓ Нет изменений для коммита" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Деплой завершен!" -ForegroundColor Green
Write-Host "📦 Репозиторий: https://github.com/imuzolev/medkit" -ForegroundColor Cyan
