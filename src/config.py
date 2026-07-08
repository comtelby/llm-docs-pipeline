import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOAD_DIR = BASE_DIR / "input" / "uploads"
INVENTORY_DIR = BASE_DIR / "inventory"
CONFIGS_DIR = BASE_DIR / "input" / "configs"
SCREENSHOTS_DIR = BASE_DIR / "input" / "screenshots"
SAMPLES_DIR = BASE_DIR / "input" / "samples"
OUTPUT_DIR = BASE_DIR / "output"
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = BASE_DIR / "data" / "audit.db"

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama:11434/api")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5-coder:7b")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
