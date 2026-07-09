# Инструкция по разворачиванию проекта из GitHub

## Требования к серверу

- Linux (Ubuntu 22.04+/Debian 12+) или Windows с WSL2
- Python 3.12+
- Docker и Docker Compose v2
- Git
- Минимум 8 GB RAM, 20 GB диска (для Ollama + моделей)

## 1. Клонирование репозитория

```bash
git clone https://github.com/comtelby/llm-docs-pipeline.git
cd llm-docs-pipeline
```

## 2. Быстрый запуск (Docker Compose)

```bash
# Создать .env из примера
cp .env.example .env

# Запустить сервисы
docker-compose up -d --build

# Проверить здоровье
curl http://localhost:8000/health
```

Сервисы:
- **Ollama** (порт 11434) — LLM-движок
- **FastAPI Bot** (порт 8000) — веб-интерфейс и API

## 3. Первоначальная настройка Ollama

После запуска необходимо загрузить LLM-модель:

```bash
# Загрузить рекомендуемую модель
docker exec ollama ollama pull qwen2.5-coder:7b

# Проверить список моделей
curl http://localhost:11434/api/tags
```

Другие поддерживаемые модели: `llama3.1:8b`, `mistral:7b`, `codellama:7b`.

## 4. Запуск без Docker (локальная разработка)

### 4.1. Установка системных зависимостей

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng antiword catdoc
```

### 4.2. Установка Python-зависимостей

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3. Запуск Ollama (отдельно)

```bash
# Установить Ollama: https://ollama.com/download
ollama pull qwen2.5-coder:7b
ollama serve
```

### 4.4. Запуск приложения

```bash
# Терминал 1: Ollama уже запущен
# Терминал 2:
source venv/bin/activate
OLLAMA_API_URL=http://localhost:11434/api uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 5. CI/CD через GitHub Actions

При пуше в ветку `main` автоматически:

1. Запускаются тесты (pytest)
2. Выполняется линтинг (ruff)
3. Собирается Docker-образ
4. Образ пушится в GitHub Container Registry (`ghcr.io/comtelby/llm-docs-pipeline`)

### На сервере: автообновление через watchtower

```bash
# Запустить watchtower для автообновления
docker run -d --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  llm-docs-pipeline-fastapi-bot ollama \
  --interval 60
```

Или обновлять вручную:

```bash
docker-compose down
docker pull ghcr.io/comtelby/llm-docs-pipeline:latest
docker-compose up -d
```

## 6. Конфигурация

| Переменная | Описание | По умолчанию |
|---|---|---|
| `OLLAMA_API_URL` | URL Ollama API | `http://ollama:11434/api` |
| `OLLAMA_DEFAULT_MODEL` | Модель LLM | `qwen2.5-coder:7b` |
| `SECRET_KEY` | Ключ для сессий | `change-me-in-production` |

## 7. Структура директорий

```
input/configs/     — конфиги сетевых устройств (.cfg, .txt, .doc, .docx, .xlsx)
input/screenshots/ — скриншоты для OCR (.png, .jpg, .gif)
input/samples/     — шаблоны отчётов (.rtf, .docx, .md)
inventory/         — справочные данные инвентаризации
output/            — сгенерированные отчёты
data/              — SQLite база данных
templates/         — HTML-шаблоны Jinja2
```

## 8. Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/health

# Список моделей Ollama
curl http://localhost:11434/api/tags

# Просмотр логов
docker-compose logs -f fastapi-bot
docker-compose logs -f ollama
```

## 9. Устранение неполадок

**Ollama не отвечает:**
```bash
docker-compose restart ollama
docker exec ollama ollama pull qwen2.5-coder:7b
```

**Конфликт портов:** измените порты в `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"   # вместо 8000:8000
```

**Ошибка Tesseract:** установите пакет:
```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```
