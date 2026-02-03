# Скрипт для первоначального деплоя проекта на сервер Beget
# Установка кодировки UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$SERVER = "root@2.56.240.119"
$REMOTE_PATH = "~/analiz_aptechki"

# Функция для проверки успешности выполнения команды
function Test-Command {
    param([string]$Command, [string]$Description)
    Write-Host "$Description..." -ForegroundColor Yellow
    try {
        $result = Invoke-Expression $Command 2>&1
        $success = $?
        if (-not $success) {
            Write-Host "Ошибка при выполнении: $Description" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
            return $false
        }
        # Дополнительная проверка через $LASTEXITCODE для внешних команд
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            Write-Host "Ошибка при выполнении: $Description (код выхода: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
            return $false
        }
        return $true
    } catch {
        Write-Host "Исключение при выполнении: $Description" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        return $false
    }
}

Write-Host "=== Деплой проекта на сервер Beget ===" -ForegroundColor Green
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

Write-Host "Все необходимые файлы найдены." -ForegroundColor Green
Write-Host ""

# Шаг 1: Создание директории на сервере
$sshCmd1 = "ssh $SERVER 'mkdir -p $REMOTE_PATH'"
if (-not (Test-Command $sshCmd1 "Шаг 1: Создание директории на сервере")) {
    Write-Host "Не удалось создать директорию на сервере. Проверьте подключение." -ForegroundColor Red
    exit 1
}

# Шаг 2: Создание файла analiz_aptechki в корне
$sshCmd2 = "ssh $SERVER 'cd ~ && touch analiz_aptechki && echo ""Проект анализа аптечки"" > analiz_aptechki'"
if (-not (Test-Command $sshCmd2 "Шаг 2: Создание файла analiz_aptechki в корне")) {
    Write-Host "Предупреждение: Не удалось создать файл analiz_aptechki в корне." -ForegroundColor Yellow
}

# Шаг 3: Загрузка файлов проекта
Write-Host "Шаг 3: Загрузка файлов проекта..." -ForegroundColor Yellow
$filesToUpload = @(
    @{Source="app.py"; Dest="${SERVER}:${REMOTE_PATH}/"},
    @{Source="requirements.txt"; Dest="${SERVER}:${REMOTE_PATH}/"},
    @{Source="templates"; Dest="${SERVER}:${REMOTE_PATH}/"; Recursive=$true},
    @{Source="static"; Dest="${SERVER}:${REMOTE_PATH}/"; Recursive=$true}
)

foreach ($file in $filesToUpload) {
    $scpCmd = if ($file.Recursive) {
        "scp -r `"$($file.Source)`" `"$($file.Dest)`""
    } else {
        "scp `"$($file.Source)`" `"$($file.Dest)`""
    }
    
    if (-not (Test-Command $scpCmd "  Загрузка $($file.Source)")) {
        Write-Host "Ошибка при загрузке $($file.Source)" -ForegroundColor Red
        exit 1
    }
}

# Шаг 4: Настройка окружения на сервере
Write-Host "Шаг 4: Настройка окружения на сервере..." -ForegroundColor Yellow

$cmd1 = 'cd ~/analiz_aptechki; if [ ! -d venv ]; then python3 -m venv venv; fi'
$cmd2 = 'cd ~/analiz_aptechki; source venv/bin/activate; pip install --upgrade pip'
$cmd3 = 'cd ~/analiz_aptechki; source venv/bin/activate; pip install -r requirements.txt'

$sshCmd3 = "ssh $SERVER '$cmd1'"
if (-not (Test-Command $sshCmd3 "  Создание виртуального окружения")) {
    Write-Host "Ошибка при создании виртуального окружения." -ForegroundColor Red
    exit 1
}

$sshCmd4 = "ssh $SERVER '$cmd2'"
if (-not (Test-Command $sshCmd4 "  Обновление pip")) {
    Write-Host "Предупреждение: Не удалось обновить pip." -ForegroundColor Yellow
}

$sshCmd5 = "ssh $SERVER '$cmd3'"
if (-not (Test-Command $sshCmd5 "  Установка зависимостей")) {
    Write-Host "Ошибка при установке зависимостей." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Деплой завершен успешно! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Следующие шаги на сервере:" -ForegroundColor Cyan
Write-Host "1. Подключитесь: ssh $SERVER" -ForegroundColor White
Write-Host "2. Перейдите: cd $REMOTE_PATH" -ForegroundColor White
Write-Host "3. Активируйте venv: source venv/bin/activate" -ForegroundColor White
Write-Host "4. Запустите: python app.py" -ForegroundColor White
Write-Host ""
Write-Host "Или используйте скрипт update.ps1 для обновления проекта." -ForegroundColor Cyan
