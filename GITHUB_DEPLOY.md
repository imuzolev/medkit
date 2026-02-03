# Инструкция по деплою на GitHub

## Шаг 1: Установка Git

Если Git не установлен, скачайте и установите его:

1. Перейдите на https://git-scm.com/download/win
2. Скачайте установщик для Windows
3. Запустите установщик и следуйте инструкциям
4. **Важно**: При установке выберите опцию "Add Git to PATH"

После установки перезапустите PowerShell или Cursor.

## Шаг 2: Проверка установки Git

Откройте PowerShell и выполните:

```powershell
git --version
```

Если команда работает, переходите к следующему шагу.

## Шаг 3: Настройка Git (первый раз)

Если вы используете Git впервые, настройте имя и email:

```powershell
git config --global user.name "Ваше Имя"
git config --global user.email "ваш.email@example.com"
```

## Шаг 4: Автоматический деплой

Запустите скрипт деплоя:

```powershell
cd D:\ivantuz\profi
.\deploy_to_github.ps1
```

## Шаг 5: Ручной деплой (альтернатива)

Если скрипт не работает, выполните команды вручную:

```powershell
# Переход в директорию проекта
cd D:\ivantuz\profi

# Инициализация git (если еще не инициализирован)
git init

# Добавление remote репозитория
git remote add origin https://github.com/imuzolev/medkit.git
# Или если remote уже существует:
# git remote set-url origin https://github.com/imuzolev/medkit.git

# Добавление всех файлов
git add .

# Создание коммита
git commit -m "Initial commit: Flask app for medkit analysis"

# Отправка на GitHub
git branch -M main
git push -u origin main
```

**Примечание**: При первом push GitHub может запросить авторизацию. Используйте:
- Personal Access Token (рекомендуется)
- Или GitHub Desktop для упрощенной работы

## Создание Personal Access Token

1. Перейдите на https://github.com/settings/tokens
2. Нажмите "Generate new token" → "Generate new token (classic)"
3. Выберите срок действия и права доступа (нужен `repo`)
4. Скопируйте токен
5. При запросе пароля используйте токен вместо пароля

## Проверка деплоя

После успешного деплоя откройте в браузере:
https://github.com/imuzolev/medkit

Все файлы должны быть видны в репозитории.

## Обновление репозитория

После внесения изменений в проект:

```powershell
cd D:\ivantuz\profi
git add .
git commit -m "Описание изменений"
git push
```
