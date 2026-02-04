# Скрипт для проверки webhook Coolify (PowerShell)

$webhookUrl = "http://2.56.240.119:8888/webhooks/source/github/events/uksoc0wgw08gk848s4kokg8c"

Write-Host "=== Тестирование webhook ===" -ForegroundColor Green
Write-Host "URL: $webhookUrl" -ForegroundColor Cyan
Write-Host ""

# Тестовый payload от GitHub (push event)
$payload = @{
    ref = "refs/heads/main"
    before = "0000000000000000000000000000000000000000"
    after = "3f6e18d1234567890abcdef1234567890abcdef"
    repository = @{
        id = 1148454109
        name = "medkit"
        full_name = "imuzolev/medkit"
    }
    pusher = @{
        name = "test"
        email = "test@example.com"
    }
} | ConvertTo-Json -Depth 10

Write-Host "Отправка POST запроса..." -ForegroundColor Yellow
Write-Host ""

try {
    $headers = @{
        "Content-Type" = "application/json"
        "X-GitHub-Event" = "push"
        "X-GitHub-Delivery" = "test-delivery-id"
    }
    
    $response = Invoke-WebRequest -Uri $webhookUrl `
        -Method POST `
        -Headers $headers `
        -Body $payload `
        -UseBasicParsing `
        -MaximumRedirection 0 `
        -ErrorAction SilentlyContinue
    
    Write-Host "Статус: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Ответ: $($response.Content)" -ForegroundColor Cyan
    
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "Статус: $statusCode" -ForegroundColor $(if ($statusCode -eq 302) { "Yellow" } else { "Red" })
    Write-Host "Ошибка: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($statusCode -eq 302) {
        Write-Host ""
        Write-Host "⚠ Webhook возвращает редирект (302)" -ForegroundColor Yellow
        Write-Host "Это означает, что требуется авторизация или URL неправильный" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Проверка завершена ===" -ForegroundColor Green
Write-Host ""
Write-Host "Ожидаемые результаты:" -ForegroundColor Cyan
Write-Host "- 200 OK = webhook работает" -ForegroundColor Green
Write-Host "- 302 = редирект (требуется авторизация)" -ForegroundColor Yellow
Write-Host "- 401/403 = требуется авторизация" -ForegroundColor Red
Write-Host "- 404 = webhook не найден" -ForegroundColor Red
