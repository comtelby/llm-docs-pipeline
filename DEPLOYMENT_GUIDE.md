# 📦 iqDataBot — Полное руководство по развертыванию

> **Версия:** 1.0  
> **Дата:** 2026-09-03  
> **Пароль для доступа к артефактам:** `Bf5555`  
> **Репозиторий:** https://github.com/your-org/iqdata-bot (замените на свой)

---

## 🎯 Что разворачивается

| Компонент | Технология | Порт |
|-----------|------------|------|
| **API / Web UI** | FastAPI + Jinja2 + Bootstrap 5 | 8000 |
| **LLM (локально)** | Ollama (qwen2.5-coder:7b по умолчанию) | 11434 |
| **База данных** | SQLite (WAL mode) | — |
| **Файловое хранилище** | Локальные директории | — |

---

## 📋 Требования к хосту

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| **CPU** | 4 vCPU | 8+ vCPU |
| **RAM** | 16 GB | 32+ GB (для 7B модели) |
| **Диск** | 30 GB SSD | 100+ GB NVMe |
| **OS** | Linux (Ubuntu 22.04+, Debian 12, RHEL 9) | Ubuntu 24.04 LTS |
| **Docker** | 24+ | 26+ |
| **Docker Compose** | v2+ | v2.24+ |

> ⚠️ **Важно:** Для работы LLM локально нужен **AVX2** (современные x86_64). На ARM (Apple Silicon, Graviton) работает через эмуляцию — медленно. Для GPU ускорения нужна NVIDIA GPU + `nvidia-container-toolkit`.

---

## 🚀 Быстрый старт (Docker Compose)

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/your-org/iqdata-bot.git
cd iqdata-bot
```

### 2. Настройте переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env под свои нужды
```

**`.env` — ключевые параметры:**

```bash
# === ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ ===
SECRET_KEY=your-very-long-random-secret-key-here-min-32-chars
OLLAMA_API_URL=http://ollama:11434/api
OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b

# === Опционально ===
# Для GPU (NVIDIA):
# OLLAMA_GPU_LAYERS=999
# Для внешнего Ollama:
# OLLAMA_API_URL=http://host.docker.internal:11434/api
```

### 3. Запустите всё одной командой

```bash
docker-compose up -d --build
```

### 4. Проверьте статус

```bash
docker-compose ps
# Ожидается: fastapi-bot (healthy), ollama (running)

docker-compose logs -f fastapi-bot
# Ждите: "Application startup complete"
```

### 5. Откройте в браузере

```
http://<IP_ВАШЕГО_СЕРВЕРА>:8000/
```

---

## 🔧 Подробная настройка

### Модели LLM — управление из UI

В интерфейсе **уже реализовано**:
- ✅ Выбор модели из выпадающего списка (`/models` endpoint)
- ✅ Список загруженных в Ollama моделей подгружается динамически
- ✅ При отправке промпта модель передаётся в `query_ollama()`

**Что НЕ реализовано (one-click pull):**
- ❌ Кнопка "Скачать модель" в UI
- ❌ Поиск моделей в библиотеке Ollama Hub

> **Workaround:** Скачивайте модели через CLI на хосте Ollama:
> ```bash
> docker exec -it ollama ollama pull qwen2.5-coder:7b
> docker exec -it ollama ollama pull llama3.1:8b
> docker exec -it ollama ollama pull mistral-nemo:12b
> ```
> После этого обновите страницу — модель появится в списке.

#### Популярные открытые модели (freeware)

| Модель | Размер | RAM (CPU) | VRAM (GPU) | Особенности |
|--------|--------|-----------|------------|-------------|
| `qwen2.5-coder:7b` | 4.7 GB | 8 GB | 6 GB | **По умолчанию**, отлично кодит |
| `qwen2.5:7b` | 4.7 GB | 8 GB | 6 GB | Общая, русскоязычная |
| `llama3.1:8b` | 4.9 GB | 8 GB | 6 GB | Meta, сильная логика |
| `mistral-nemo:12b` | 7.1 GB | 16 GB | 8 GB | 128k контекст, мультиязык |
| `phi3:14b` | 7.9 GB | 16 GB | 8 GB | Microsoft, компактная |
| `gemma2:9b` | 5.4 GB | 12 GB | 6 GB | Google, хорошая русская |
| `deepseek-coder:6.7b` | 3.8 GB | 8 GB | 5 GB | Спец. под код |

> 💡 Для отчётов на русском лучше всего: **qwen2.5:7b**, **gemma2:9b**, **mistral-nemo:12b**.

### Переменные окружения (полный список)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `SECRET_KEY` | — | **Обязательно!** Секрет для сессий/JWT |
| `OLLAMA_API_URL` | `http://ollama:11434/api` | URL Ollama API |
| `OLLAMA_DEFAULT_MODEL` | `qwen2.5-coder:7b` | Модель по умолчанию |
| `DATABASE_URL` | `sqlite:///data/audit.db` | Путь к БД (не меняйте в Docker) |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

---

## 🏗️ Архитектура директорий (в контейнере)

```
/app
├── input/
│   ├── uploads/      # Чеклисты (CSV)
│   ├── configs/      # Сетевые конфиги (временные)
│   ├── screenshots/  # Скриншоты для OCR (временные)
│   └── samples/      # Шаблоны отчётов (накопительные)
├── inventory/        # Справочные данные (накопительные)
├── output/           # Сгенерированные отчёты
├── storage/          # Внутреннее хранилище
│   └── report-templates/
└── data/
    └── audit.db      # SQLite БД
```

> **Политика очистки:** Кнопка "Очистить временные данные" удаляет только `configs/` и `screenshots/`. `inventory/` и `samples/` сохраняются навсегда.

---

## 🐳 Production-варианты развертывания

### Вариант А: Docker Compose (рекомендуется для 1 сервера)

```bash
# Уже описано выше — docker-compose up -d
```

### Вариант Б: Systemd + отдельный Ollama (для масштабирования)

**На хосте с GPU (Ollama):**
```bash
# Установка Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Как systemd сервис (уже сделано установщиком)
systemctl enable ollama
systemctl start ollama

# Скачайте модели
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
```

**На хосте приложения (FastAPI):**
```bash
# Python 3.12+
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env с внешним Ollama
echo "OLLAMA_API_URL=http://<OLLAMA_HOST>:11434/api" > .env

# Запуск
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Systemd unit для FastAPI:**
```ini
# /etc/systemd/system/iqdatabot.service
[Unit]
Description=iqDataBot FastAPI
After=network.target

[Service]
Type=exec
User=iqdatabot
WorkingDirectory=/opt/iqdatabot
EnvironmentFile=/opt/iqdatabot/.env
ExecStart=/opt/iqdatabot/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Вариант В: Kubernetes (Helm chart — будущее)

> Планируется: Helm chart с отдельными Deployment для API и Ollama, PVC для данных, Ingress с TLS.

---

## 🔐 Безопасность

### Обязательные действия перед продакшеном

1. **Смените SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   # Вставьте в .env
   ```

2. **Настройте Reverse Proxy (Nginx/Traefik/Caddy) с HTTPS:**
   ```nginx
   # Nginx пример
   server {
       listen 443 ssl http2;
       server_name iqbot.yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/iqbot.yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/iqbot.yourdomain.com/privkey.pem;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 300s;  # Важно для долгой генерации отчётов
           proxy_send_timeout 300s;
       }
   }
   ```

3. **Ограничьте доступ к портам:**
   - `8000` — только через Reverse Proxy
   - `11434` (Ollama) — **только локально/VPN**, не expon'ьте в интернет!

4. **Файрвол:**
   ```bash
   ufw allow 22/tcp   # SSH
   ufw allow 80/tcp   # HTTP -> редирект на 443
   ufw allow 443/tcp  # HTTPS
   ufw enable
   ```

---

## 📊 Мониторинг и логи

### Логи приложения
```bash
# Docker
docker-compose logs -f fastapi-bot --tail=100

# Systemd
journalctl -u iqdatabot -f --since "1 hour ago"
```

### Health checks
```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl http://localhost:11434/api/tags
# {"models": [...]}
```

### Метрики (Prometheus — опционально)
Добавьте в `src/main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

---

## 🛠️ Обслуживание

### Обновление кода
```bash
cd /opt/iqdatabot  # или папка проекта
git pull
docker-compose up -d --build
# или для systemd:
source venv/bin/activate
pip install -r requirements.txt
systemctl restart iqdatabot
```

### Обновление моделей Ollama
```bash
docker exec ollama ollama pull qwen2.5-coder:7b
# Перезагрузка не нужна — модель подхватится при следующем запросе
```

### Бэкап БД и данных
```bash
# SQLite бэкап (online, بفضل WAL)
docker exec fastapi-bot sqlite3 /app/data/audit.db ".backup /app/data/audit_backup_$(date +%F).db"

# Полный бэкап директорий
tar -czf iqdatabot_backup_$(date +%F).tar.gz \
    data/ inventory/ input/samples/ output/ storage/
```

### Очистка старых отчётов
```bash
# Удаление отчётов старше 90 дней
find /app/output -name "*.md" -mtime +90 -delete
```

---

## ❗ Troubleshooting

| Проблема | Решение |
|----------|---------|
| `Ollama недоступна` в UI | Проверьте `docker-compose ps ollama`, логи: `docker-compose logs ollama` |
| Долгая генерация отчёта (>5 мин) | Увеличьте `timeout` в `query_ollama()`, `num_predict` уменьшите |
| OOM (Out of Memory) | Меньшая модель (`phi3:3.8b`), `--gpu-layers`, больше RAM |
| БД locked | Только 1 экземпляр FastAPI на 1 БД. Используйте PostgreSQL для кластера |
| Кириллица в PDF не отображается | Установите шрифты: `apt install fonts-dejavu-core` |
| Модель не скачивается | Проверьте диск: `df -h`, права на `/root/.ollama` |

---

## 📝 Чек-лист перед go-live

- [ ] `SECRET_KEY` сгенерирован и в `.env`
- [ ] HTTPS настроен (Let's Encrypt / самоподписанный)
- [ ] Ollama доступен только локально/VPN
- [ ] Модели загружены: `ollama list`
- [ ] Бэкап настроен (cron/systemd timer)
- [ ] Логи ротируются (logrotate / docker logging driver)
- [ ] Порт 8000 не открыт во внешний мир
- [ ] Протестирована генерация отчёта с реальными данными
- [ ] Пароль `Bf5555` 전달ён ответственному лицу

---

## 🔗 Полезные ссылки

- **Ollama модели:** https://ollama.com/library
- **FastAPI docs:** https://fastapi.tiangolo.com
- **Docker Compose spec:** https://docs.docker.com/compose/compose-file/
- **Nginx reverse proxy:** https://nginx.org/en/docs/http/load_balancing.html

---

## 📞 Поддержка

При проблемах:
1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь в ресурсах: `docker stats`
3. Создайте Issue в репозитории с логами и описанием окружения

---

*Документ создан автоматически на основе кодовой базы iqDataBot v1.0*