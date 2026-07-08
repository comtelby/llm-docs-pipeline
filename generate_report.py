import os
import json
from pathlib import Path
from llama_index.core import Document, VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Настройка LLM и эмбеддингов
llm = Ollama(model="qwen2.5-coder:7b", base_url="http://localhost:11434/v1")
embed_model = OllamaEmbedding(model_name="nomic-embed-text", base_url="http://localhost:11434/v1")

def load_documents(dir_path: str) -> list[Document]:
    if not os.path.exists(dir_path):
        return []
    reader = SimpleDirectoryReader(input_dir=dir_path)
    return reader.load_data()

def build_index(docs: list[Document]) -> VectorStoreIndex:
    return VectorStoreIndex.from_documents(docs, embed_model=embed_model)

def get_template(template_name: str = "default_json.md") -> str:
    template_path = BASE_DIR / "storage" / "report-templates" / template_name
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Шаблон по умолчанию, если файл не найден
    return """
# Отчёт по аудиту конфигурации

## Общие сведения
- Дата формирования: {date}
- Источник данных: {source_summary}

## Найденные устройства и параметры
{devices_json}

## Противоречия и замечания
{issues}
"""

def generate_report():
    # 1. Загружаем глобальные знания (универсальные справочники)
    global_docs = load_documents("storage/global-knowledge")

    # 2. Загружаем конфиги и скриншоты конкретного объекта
    config_docs = load_documents("input/configs")
    screenshot_docs = load_documents("input/screenshots")  # LlamaIndex умеет передавать картинки в мультимодальные модели

    all_docs = global_docs + config_docs + screenshot_docs

    if not all_docs:
        print("Нет документов для анализа. Положи файлы в input/configs или input/screenshots.")
        return

    # Строим индекс (RAG)
    index = build_index(all_docs)
    query_engine = index.as_query_engine(llm=llm, similarity_top_k=5)

    # Промпт с привязкой к шаблону и структуре
    prompt = get_template("default_json.md").format(
        date="2024-10-01",
        source_summary=f"Конфиги: {len(config_docs)}, Скриншоты: {len(screenshot_docs)}, Глобал: {len(global_docs)}"
    )

    instruction = (
        "Ты — инженер по аудиту ИТ‑инфраструктуры. Проанализируй найденные фрагменты документации "
        "и сформируй отчёт по оборудованию. Для каждого устройства укажи: модель, серийный номер (если есть), "
        "роль, IP‑адрес, VLAN, статус, источник данных (файл/тип). Ответ верни строго в формате JSON. "
        "Если в данных есть противоречия — укажи их отдельным списком."
    )

    response = query_engine.query(instruction)
    result_text = str(response)

    # Сохраняем отчёт в output/
    output_path = BASE_DIR / "output" / "audit_report.json"
    # Если ответ уже JSON — сохраняем как JSON; если нет — пытаемся распарсить
    try:
        data = json.loads(result_text.strip())
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Отчёт сохранён в JSON: {output_path}")
    except Exception:
        # Если не JSON — сохраняем как текст
        txt_path = BASE_DIR / "output" / "audit_report.md"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result_text)
        print(f"Отчёт сохранён как текст: {txt_path}")

if __name__ == "__main__":
    generate_report()
