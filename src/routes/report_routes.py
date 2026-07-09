import markdown
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse

import aiofiles

from src.config import OUTPUT_DIR
from src.database import list_audit_history
from src.report import generate_report

from src.state import get_last_prompt

router = APIRouter()


@router.post("/generate-report")
async def create_report():
    prompt = get_last_prompt()
    if not prompt:
        raise HTTPException(400, "Сначала сформулируйте задачу в чате")
    result = await generate_report(prompt)
    return result


@router.get("/reports")
async def list_reports():
    reports = []
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.iterdir():
            if f.is_file():
                s = f.stat()
                from datetime import datetime
                reports.append({
                    "name": f.name,
                    "size_bytes": s.st_size,
                    "modified": datetime.fromtimestamp(s.st_mtime).isoformat()
                })
    return {"reports": sorted(reports, key=lambda x: x["modified"], reverse=True)}


@router.get("/download/{filename}")
async def download_report(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Файл не найден")
    return FileResponse(str(path), filename=filename)


@router.get("/view/{filename}")
async def view_report(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Файл не найден")
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()
    return {"filename": filename, "content": content}


@router.get("/export/{filename}")
async def export_report(filename: str, format: str = "md"):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Файл не найден")
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()

    if format == "md":
        return FileResponse(str(path), filename=filename)
    elif format == "txt":
        return PlainTextResponse(
            content,
            headers={"Content-Disposition": f"attachment; filename={filename.replace('.md', '.txt')}"}
        )
    elif format == "html":
        html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        return HTMLResponse(
            f"<html><head><meta charset='UTF-8'>"
            f"<style>body{{font-family:Arial;max-width:900px;margin:40px auto;padding:20px}}"
            f"table{{border-collapse:collapse;width:100%}}"
            f"td,th{{border:1px solid #ddd;padding:8px}}</style>"
            f"</head><body>{html}</body></html>"
        )
    else:
        raise HTTPException(400, f"Формат {format} не поддерживается")


@router.get("/audit-history")
async def get_audit_history():
    return {"history": list_audit_history()}
