from fastapi import APIRouter, HTTPException, UploadFile

from src.checklist import (
    get_checklist_summary,
    match_files_to_checklist,
    parse_checklist_csv,
)
from src.config import BASE_DIR
from src.eol import add_to_eol_database, get_eol_stats
from src.parser import classify_and_parse, extract_text_from_file

router = APIRouter()


@router.get("/checklist/progress")
async def checklist_progress():
    csv_path = BASE_DIR / "input" / "checklist.csv"
    if not csv_path.exists():
        csv_path = BASE_DIR / "input" / "uploads" / "checklist.csv"
    if not csv_path.exists():
        raise HTTPException(404, "Файл чеклиста не найден. Загрузите checklist.csv в input/")

    items = parse_checklist_csv(csv_path)
    if not items:
        raise HTTPException(400, "Чеклист пуст или содержит ошибки")

    summary = get_checklist_summary(items)
    return summary


@router.get("/checklist/export")
async def checklist_export():
    csv_path = BASE_DIR / "input" / "checklist.csv"
    if not csv_path.exists():
        csv_path = BASE_DIR / "input" / "uploads" / "checklist.csv"
    if not csv_path.exists():
        raise HTTPException(404, "Файл чеклиста не найден")

    items = parse_checklist_csv(csv_path)
    if not items:
        raise HTTPException(400, "Чеклист пуст")

    from src.checklist import export_checklist_status
    csv_content = export_checklist_status(items)
    return {"format": "csv", "content": csv_content, "items_count": len(items)}


@router.post("/checklist/upload")
async def upload_checklist(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Чеклист должен быть в формате CSV")

    save_dir = BASE_DIR / "input" / "uploads"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / "checklist.csv"

    content = await file.read()
    save_path.write_bytes(content)

    items = parse_checklist_csv(save_path)
    summary = get_checklist_summary(items)

    return {
        "status": "success",
        "filename": file.filename,
        "total_items": summary["total_items"],
        "completed_items": summary["completed_items"],
        "overall_completion_pct": summary["overall_completion_pct"],
    }


@router.post("/checklist/match-files")
async def match_files_to_checklist_endpoint():
    csv_path = BASE_DIR / "input" / "checklist.csv"
    if not csv_path.exists():
        csv_path = BASE_DIR / "input" / "uploads" / "checklist.csv"
    if not csv_path.exists():
        raise HTTPException(404, "Файл чеклиста не найден")

    items = parse_checklist_csv(csv_path)

    all_files = []
    for subdir in ["configs", "screenshots", "samples", "inventory"]:
        dir_path = BASE_DIR / "input" / subdir
        if dir_path.exists():
            for f in dir_path.iterdir():
                if f.is_file():
                    all_files.append(f.name)

    matches = match_files_to_checklist(items, all_files)

    return {
        "total_files": len(all_files),
        "total_matches": len(matches),
        "matches": matches[:50],
    }


@router.get("/eol/stats")
async def eol_statistics():
    return get_eol_stats()


@router.post("/eol/add")
async def add_eol_record(
    model: str,
    vendor: str = "",
    category: str = "",
    eol: str = "",
    status: str = "Требуется проверка",
    note: str = "",
):
    added = add_to_eol_database(model, vendor, category, eol, status, note)
    return {
        "status": "added" if added else "updated",
        "model": model,
        "total_records": len(get_eol_stats()["by_status"]),
    }


@router.get("/analyze/files")
async def analyze_uploaded_files():
    results = []
    for subdir in ["configs", "screenshots", "samples", "inventory"]:
        dir_path = BASE_DIR / "input" / subdir
        if not dir_path.exists():
            continue
        for f in dir_path.iterdir():
            if not f.is_file():
                continue
            text = extract_text_from_file(f)
            if text and len(text) > 50:
                _, file_type = classify_and_parse(text, f.name)
                results.append({
                    "filename": f.name,
                    "directory": subdir,
                    "detected_type": file_type,
                    "size_bytes": f.stat().st_size,
                    "text_preview": text[:200],
                })
    return {
        "total_files": len(results),
        "files": results,
    }


@router.get("/collectors/scripts")
async def list_collector_scripts():
    collectors_dir = BASE_DIR / "src" / "collectors"
    if not collectors_dir.exists():
        return {"scripts": []}

    scripts = []
    for f in collectors_dir.iterdir():
        if f.is_file() and f.suffix in (".ps1", ".sh"):
            scripts.append({
                "name": f.name,
                "platform": "Windows" if f.suffix == ".ps1" else "Linux",
                "description": _get_script_description(f.name),
            })
    return {"scripts": scripts}


def _get_script_description(filename: str) -> str:
    descriptions = {
        "windows_server.ps1": "Сбор данных с Windows-сервера (systeminfo, диски, роли, службы)",
        "linux_server.sh": "Сбор данных с Linux-сервера (lscpu, df, systemctl, dmesg)",
        "vmware_esxi.sh": "Сбор данных с ESXi-хоста (VMs, storage, networking, HA)",
        "hyper_v.ps1": "Сбор данных Hyper-V (хосты, ВМ, кластеры, хранилища)",
        "backup_collect.ps1": "Сбор данных о системе резервного копирования (Veeam/Acronis/WSB)",
    }
    return descriptions.get(filename, "Скрипт сбора данных")
