import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile

from src.config import (
    CONFIGS_DIR,
    INVENTORY_DIR,
    OUTPUT_DIR,
    SAMPLES_DIR,
    SCREENSHOTS_DIR,
)
from src.database import upsert_inventory
from src.parser import parse_inventory_rows

logger = __import__("logging").getLogger(__name__)

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
                        "modified": datetime.fromtimestamp(s.st_mtime, tz=timezone.utc).isoformat()
                    })
    return files_info


async def save_upload(category: str, file: UploadFile) -> str:
    if category not in CATEGORY_DIR_MAP:
        raise HTTPException(400, "Неизвестная категория")
    path = CATEGORY_DIR_MAP[category] / f"{uuid.uuid4().hex}_{file.filename}"
    async with aiofiles.open(path, "wb") as buf:
        content = await file.read()
        await buf.write(content)

    if category == "inventory":
        _import_inventory_to_db(path, file.filename)

    return file.filename


def _import_inventory_to_db(file_path: Path, original_name: str) -> dict:
    rows = parse_inventory_rows(file_path)
    updated_count = 0
    inserted_count = 0
    for rec in rows:
        updated = upsert_inventory(
            model=rec["model"],
            vendor=rec["vendor"],
            category=rec["category"],
            eol=rec["eol"],
            eol_status=rec["eol_status"],
            specs=rec["specs"],
            source_url=original_name,
        )
        if updated:
            updated_count += 1
        else:
            inserted_count += 1
    logger.info(
        f"Импорт из {original_name}: {inserted_count} новых, {updated_count} обновлено"
    )
    return {"inserted": inserted_count, "updated": updated_count}


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
