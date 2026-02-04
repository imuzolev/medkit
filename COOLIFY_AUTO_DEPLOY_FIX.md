# Настройка автоматического деплоя в Coolify

## Текущая ситуация

✅ Репозиторий подключен: `imuzolev/medkit`  
✅ Ветка: `main`  
❌ Автоматический деплой не работает (webhook с `/manual`)

## Решение: Найти автоматический webhook

В Coolify при подключении GitHub через OAuth автоматически создается webhook. Нужно найти его правильный URL.

### Способ 1: Проверить раздел "General"

1. В Coolify UI откройте ваше приложение
2. Перейдите в раздел **"General"** (в левом меню)
3. Ищите настройки:
   - **"Auto Deploy"** - должна быть включена ✅
   - **"Deploy on Push"** - должна быть включена ✅
4. Если эти опции есть, включите их и сохраните

### Способ 2: Проверить через GitHub

Coolify может автоматически создать webhook в GitHub при подключении:

1. Откройте: `https://github.com/imuzolev/medkit/settings/hooks`
2. Проверьте, есть ли там webhook от Coolify (автоматически созданный)
3. Если есть, проверьте его URL - он должен быть БЕЗ `/manual`
4. Если нет автоматического webhook, нужно создать его вручную

### Способ 3: Использовать автоматический webhook URL

Правильный формат автоматического webhook в Coolify обычно:
```
http://2.56.240.119:8888/webhooks/source/github/events/<application_uuid>
```

Где `<application_uuid>` - это UUID вашего приложения (например, `uksoc0wgw08gk848s4kokg8c`)

Попробуйте использовать:
```
http://2.56.240.119:8888/webhooks/source/github/events/uksoc0wgw08gk848s4kokg8c
```

### Способ 4: Переподключить GitHub

1. В разделе "Git Source" нажмите "Change Git Source"
2. Отключите текущее подключение
3. Подключите заново через "Connect GitHub"
4. При подключении убедитесь, что включена опция "Auto Deploy"
5. Coolify должен автоматически создать правильный webhook

## Быстрое решение: Использовать кнопку "Deploy"

Пока автоматический деплой не настроен, можно использовать ручной деплой:

1. После каждого `git push`
2. Откройте Coolify UI
3. Нажмите кнопку **"Deploy"** (справа вверху)
4. Coolify получит последний commit и задеплоит

## Проверка работы автоматического деплоя

После настройки:

1. Сделайте небольшое изменение в коде
2. Commit и push:
   ```bash
   git add .
   git commit -m "Test auto deploy"
   git push
   ```
3. В Coolify UI должен автоматически начаться деплой
4. В GitHub webhooks должен быть успешный запрос

## Альтернатива: Использовать Deploy Webhook API

Если автоматический webhook не работает, можно использовать "Deploy Webhook" из раздела "Webhooks":

URL: `http://2.56.240.119:8888/api/v1/deploy?uuid=uksoc0wgw08gk848s4kokg8c&force=false`

Этот URL можно использовать в GitHub Actions для автоматического деплоя:

```yaml
name: Deploy to Coolify

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Coolify deployment
        run: |
          curl -X POST "http://2.56.240.119:8888/api/v1/deploy?uuid=uksoc0wgw08gk848s4kokg8c&force=false"
```

Но для этого нужна авторизация (токен).
