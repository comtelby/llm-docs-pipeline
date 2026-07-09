@echo off
chcp 1251 >nul
title iqData Bot - Аудит ИТ-инфраструктуры

echo ============================================
echo   iqData Bot - Запуск проекта
echo ============================================
echo.

:: Переход в директорию проекта (где лежит .bat)
cd /d "%~dp0"

:: Проверка Docker
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Docker не найден.
    echo Установите Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Docker Engine не запущен.
    echo Запустите Docker Desktop и повторите попытку.
    pause
    exit /b 1
)

:: Определяем команду docker compose (Docker Desktop v4+ использует docker compose, не docker-compose)
set DOCKER_COMPOSE=docker compose
docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set DOCKER_COMPOSE=docker-compose
    docker-compose version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ОШИБКА] Ни docker compose, ни docker-compose не найдены.
        pause
        exit /b 1
    )
)

:: Проверка curl (на Windows 10 1803+ / 11 встроен)
set CURL=curl
where curl >nul 2>&1 || where curl.exe >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] curl не найден.
    pause
    exit /b 1
)

echo Docker:   OK
echo Compose:  %DOCKER_COMPOSE%
echo.

:: Шаг 1 — остановка старых контейнеров
echo [1/4] Остановка старых контейнеров...
%DOCKER_COMPOSE% down 2>nul
echo.

:: Шаг 2 — сборка и запуск
echo [2/4] Сборка и запуск контейнеров...
%DOCKER_COMPOSE% up -d --build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось запустить контейнеры.
    pause
    exit /b 1
)
echo.

:: Шаг 3 — ожидание Ollama
echo [3/4] Ожидание Ollama...
:wait_ollama
timeout /t 3 /nobreak >nul
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% neq 0 goto wait_ollama
echo Ollama готова.
echo.

:: Шаг 4 — проверка модели
echo [4/4] Проверка модели LLM...
curl -s http://localhost:11434/api/tags | findstr "qwen2.5-coder" >nul
if %ERRORLEVEL% neq 0 (
    echo Модель qwen2.5-coder:7b не найдена. Загрузка...
    docker exec ollama ollama pull qwen2.5-coder:7b
) else (
    echo Модель qwen2.5-coder:7b уже загружена.
)
echo.

echo ============================================
echo   Проект запущен!
echo   http://localhost:8000
echo ============================================
echo.
echo Нажмите любую клавишу для открытия в браузере...
pause >nul

:: Открытие в браузере
start http://localhost:8000