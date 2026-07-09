import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException

from src.config import INVENTORY_DIR, CONFIGS_DIR, SCREENSHOTS_DIR, SAMPLES_DIR, OUTPUT_DIR

CATEGORY_DIR_MAP = {
    "inventory": INVENTORY_DIR,
    "configs": CONFIGS_DIR,
    "screenshots": SCREENSHOTS_DIR,
    "samples": SAMPLES_DIR,
    "reports": OUTPUT_DIR,
}

TEMP_CATEGORIES = {"configs", "screenshots"}


def _resolve_path(category: str, filename: str) -> Path:
    if category not in CATEGORY_DIR_MAP:
        raise HTTPException(400, "Неизвестная категория")
    base = CATEGORY_DIR_MAP[category]
    resolved = (base / filename).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise HTTPException(400, "Недопустимый путь к файлу")
    return resolved


def list_files() -> dict:
    files_info = {cat: [] for cat in CATEGORY_DIR_MAP}
    for category, directory in CATEGORY_DIR_MAP.items():
        if directory.exists():
            for f in directory.iterdir():
                if f.is_file():
                    s = f.stat()
                    files_info[category].append({
                        "name": f.name,
                        "size_bytes": s.st_size,
                        "modified": datetime.fromtimestamp(s.st_mtime).isoformat()
                    })
    return files_info


async def save_upload(category: str, file: UploadFile) -> str:
    if category not in CATEGORY_DIR_MAP:
        raise HTTPException(400, "Неизвестная категория")
    path = CATEGORY_DIR_MAP[category] / f"{uuid.uuid4().hex}_{file.filename}"
    with open(path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return file.filename


def delete_file(category: str, filename: str):
    path = _resolve_path(category, filename)
    if path.exists():
        os.remove(path)


def clear_temp() -> dict:
    counts = {}
    for cat in TEMP_CATEGORIES:
        d = CATEGORY_DIR_MAP[cat]
        count = 0
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    os.remove(f)
                    count += 1
        counts[cat] = count
    return counts
