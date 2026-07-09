@echo off
chcp 65001 >nul
title iqData Bot - Запуск проекта

echo ============================================
echo   iqData Bot - Аудит ИТ-инфраструктуры
echo   Запуск проекта
echo ============================================
echo.

:: Проверка Docker Desktop
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Docker не найден. Установите Docker Desktop:
    echo https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: Проверка, что Docker запущен
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Docker Engine не запущен.
    echo Запустите Docker Desktop и повторите попытку.
    pause
    exit /b 1
)

:: Переход в директорию проекта
cd /d "%~dp0"

:: Остановка старых контейнеров
echo [1/4] Остановка старых контейнеров...
docker-compose down 2>nul

:: Сборка и запуск контейнеров
echo [2/4] Сборка и запуск контейнеров...
docker-compose up -d --build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось запустить контейнеры.
    pause
    exit /b 1
)

:: Ожидание готовности Ollama
echo [3/4] Ожидание Ollama...
:wait_ollama
timeout /t 5 /nobreak >nul
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% neq 0 goto wait_ollama

:: Проверка наличия модели
echo [4/4] Проверка модели LLM...
curl -s http://localhost:11434/api/tags | findstr "qwen2.5-coder" >nul
if %ERRORLEVEL% neq 0 (
    echo Модель qwen2.5-coder:7b не найдена. Загрузка...
    docker exec ollama ollama pull qwen2.5-coder:7b
)

echo.
echo ============================================
echo   Проект запущен!
echo   Откройте браузер: http://localhost:8000
echo   Health check:    http://localhost:8000/health
echo ============================================
echo.
echo Нажмите любую клавишу для открытия в браузере...
pause >nul

:: Открытие в браузере
start http://localhost:8000
