@echo off
chcp 1251 >nul
title iqData Bot - Запуск проекта

echo ============================================
echo   iqData Bot - Аудит ИТ-инфраструктуры
echo   Запуск проекта
echo ============================================
echo.

cd /d "%~dp0"

where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [Oshibka] Docker ne naiden. Ustanovite Docker Desktop.
    pause
    exit /b 1
)

docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [Oshibka] Docker Engine ne zapushchen. Zapustite Docker Desktop.
    pause
    exit /b 1
)

set DOCKER_COMPOSE=docker compose
docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set DOCKER_COMPOSE=docker-compose
    docker-compose version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [Oshibka] docker compose ne naiden.
        pause
        exit /b 1
    )
)

set CURL=curl
where curl >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where curl.exe >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [Oshibka] curl ne naiden.
        pause
        exit /b 1
    )
    set CURL=curl.exe
)

echo Docker:  OK
echo Compose: %DOCKER_COMPOSE%
echo.

echo [1/4] Ostanovka starykh konteinerov...
%DOCKER_COMPOSE% down 2>nul
echo.

echo [2/4] Sborka i zapusk konteinerov...
%DOCKER_COMPOSE% up -d --build
if %ERRORLEVEL% neq 0 (
    echo [Oshibka] Ne udalos zapustit konteinery.
    pause
    exit /b 1
)
echo.

echo [3/4] Ozhidanie Ollama...
:wait_ollama
timeout /t 3 /nobreak >nul
%CURL% -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% neq 0 goto wait_ollama
echo Ollama gotova.
echo.

echo [4/4] Proverka modeli LLM...
%CURL% -s http://localhost:11434/api/tags | findstr "qwen2.5-coder" >nul
if %ERRORLEVEL% neq 0 (
    echo Model qwen2.5-coder:7b ne naidena. Zagruzka...
    docker exec ollama ollama pull qwen2.5-coder:7b
) else (
    echo Model qwen2.5-coder:7b uzhe zagruzhena.
)
echo.

echo ============================================
echo   Proekt zapushchen!
echo   http://localhost:8000
echo ============================================
echo.
echo Nazhmite lyubuyu klavishu dlya otkrytiya v brauzere...
pause >nul

start http://localhost:8000
