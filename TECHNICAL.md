# Техническая документация: iqData Bot

## Архитектура

```
┌─────────────────────────────────────────────────┐
│                   FastAPI App                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │   UI     │ │  Files   │ │  Report Generator │  │
│  │ (Jinja2) │ │  Upload  │ │  (LLM + шаблоны) │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │  Chat    │ │  Config  │ │  Database (CRUD) │  │
│  │ (Ollama) │ │  Parser  │ │  (SQLite)        │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
└──────────────────────┬──────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────┐
│              Ollama (LLM)                        │
│        qwen2.5-coder:7b / llama3.1:8b           │
└─────────────────────────────────────────────────┘
```

## Компоненты

### 1. Модуль `src/main.py`
Точка входа приложения FastAPI. Инициализирует роутеры, CORS, БД при старте.

**Эндпоинты:**

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | Проверка состояния сервиса |
| GET | `/` | Главная страница (Jinja2) |
| GET | `/reports-page` | Страница отчётов |
| GET | `/models` | Список моделей Ollama |
| POST | `/chat` | Отправка запроса в Ollama |
| GET | `/files` | Список загруженных файлов |
| POST | `/upload/{category}` | Загрузка файла |
| DELETE | `/files/{category}/{name}` | Удаление файла |
| POST | `/clear-temp` | Очистка временных файлов |
| POST | `/generate-report` | Генерация отчёта |
| GET | `/reports` | Список отчётов |
| GET | `/download/{filename}` | Скачивание отчёта |
| GET | `/view/{filename}` | Просмотр отчёта |
| GET | `/export/{filename}?format=md\|txt\|html` | Экспорт отчёта |
| GET | `/audit-history` | История аудитов |

### 2. Модуль `src/config.py`
Конфигурация путей и переменных окружения:

- `BASE_DIR` — корень проекта
- `TEMPLATES_DIR` — HTML-шаблоны Jinja2
- `INVENTORY_DIR` — данные инвентаризации
- `CONFIGS_DIR` — конфиги устройств
- `SCREENSHOTS_DIR` — скриншоты для OCR
- `SAMPLES_DIR` — шаблоны отчётов
- `OUTPUT_DIR` — сгенерированные отчёты
- `DB_PATH` — SQLite база данных
- `OLLAMA_API_URL` — URL Ollama API
- `OLLAMA_DEFAULT_MODEL` — модель по умолчанию

### 3. Модуль `src/parser.py`
Парсинг конфигураций сетевых устройств и извлечение текста из файлов:

**`parse_device_config(text, filename) -> DeviceInfo`**
Извлекает: hostname, модель, IP, интерфейсы, VLAN, маршруты, OSPF, VRRP, STP, AAA, ACL, NTP, SNMP.

**`extract_text_from_file(file_path) -> str`**
Универсальный диспетчер по расширению:
- `.docx` → python-docx
- `.doc` → antiword / catdoc / olefile
- `.xlsx` → openpyxl
- `.xls` → xlrd / pandas
- `.rtf` → striprtf
- `.txt/.md/.cfg/.conf/.csv` → чтение с автоопределением кодировки

**`extract_text_from_image(image_path) -> str`**
OCR через Tesseract (rus+eng) для `.png`, `.jpg`, `.gif`.

### 4. Модуль `src/report.py`
Генерация отчётов:

1. Чтение всех источников: конфиги устройств, шаблоны, inventory, OCR скриншотов
2. Анализ EOL-статусов, безопасности (AAA, NTP, ACL)
3. Классификация устройств (core/dist/access/edge)
4. LLM-генерация по структуре шаблона или fallback на стандартную
5. Раздел ADDS (LLM-анализ OCR скриншотов)
6. Раздел инвентаризации
7. Заключение с LLM-анализом
8. Сохранение в Markdown + запись в audit_history

### 5. Модуль `src/eol.py`
База данных End-of-Life для ~40 моделей оборудования (Cisco, HP, Huawei, IBM, Synology, Dell, APC, Lenovo). Функция `lookup_eol()` ищет по hostname и модели.

### 6. Модуль `src/database.py`
SQLite CRUD:
- `init_db()` — создание таблиц (inventories, audit_history, users)
- `seed_eol_to_inventories()` — заполнение inventory из EOL_DATABASE
- CRUD для inventories (list, add, delete, find)
- CRUD для audit_history (save, list)

### 7. Модуль `src/llm.py`
Интеграция с Ollama API:
- `query_ollama()` — отправка промпта, получение ответа (с параметрами temperature, num_predict, timeout)
- `list_ollama_models()` — список доступных моделей

### 8. Модуль `src/storage.py`
Управление файлами по категориям:
- `inventory`, `configs`, `screenshots`, `samples`, `reports`
- Загрузка, удаление, очистка временных директорий
- Защита от path traversal

### 9. Модуль `src/models.py`
Pydantic-модели: `DeviceInfo`, `ScreenshotData`, `ChatRequest`, `ChatResponse`, `FileInfo`, `ReportResult`, `EOLRecord`, `InventoryRecord`.

## Шаблоны отчётов

Поддерживаются три формата заголовков разделов:
1. **Markdown**: `#`, `##`, `###`
2. **Нумерованные**: `1. ЗАГОЛОВОК`, `2. РАЗДЕЛ`
3. **Прописные**: `ВВЕДЕНИЕ`, `АНАЛИЗ`

Если шаблон не найден — используется стандартная структура из 8 разделов.

## OCR-анализ

Скриншоты проходят OCR (Tesseract rus+eng), затем LLM анализирует:
- Active Directory, DHCP, DNS
- Производительность Windows
- Безопасность

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
1. **test** — pytest + ruff на ubuntu-latest, Python 3.12
2. **docker** — сборка и пуш в ghcr.io (теги: `latest`, `main-{sha}`)

## Тестирование

```
pytest tests/ -v
```

28 тестов покрывают: парсер конфигов (Cisco, HP, Huawei), извлечение текста (docx, xlsx, xls, rtf, txt), EOL-анализ, шаблонные секции, CRUD БД.

## Безопасность

- CORS открыт для всех origins (настроить в production)
- Path traversal защита в storage.py
- SECRET_KEY должен быть изменён в production
- Все пароли/токены через переменные окружения
