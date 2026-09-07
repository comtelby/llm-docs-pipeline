import io

import aiofiles
import markdown
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, StreamingResponse

from src.config import OUTPUT_DIR
from src.database import list_audit_history
from src.report import generate_report
from src.state import get_last_prompt

# PDF export (weasyprint)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

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
                from datetime import datetime, timezone
                reports.append({
                    "name": f.name,
                    "size_bytes": s.st_size,
                    "modified": datetime.fromtimestamp(s.st_mtime, tz=timezone.utc).isoformat()
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
    elif format == "docx":
        return await _export_docx(content, filename)
    elif format == "pdf":
        return await _export_pdf(content, filename)
    else:
        raise HTTPException(400, f"Формат {format} не поддерживается. Доступные: md, txt, html, docx, pdf")


def _md_to_docx(content: str, buf: io.BytesIO):
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if line.startswith(('# ', '## ', '### ')):
            level = len(line) - len(line.lstrip('#'))
            heading_text = line.lstrip('# ').strip()
            if level <= 1:
                doc.add_heading(heading_text, level=1)
            elif level == 2:
                doc.add_heading(heading_text, level=2)
            else:
                doc.add_heading(heading_text, level=3)

        elif line.startswith('|') and line.endswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip())
                i += 1
            i -= 1
            if len(rows) >= 2:
                table = doc.add_table(rows=len(rows) - 1, cols=len(rows[0].split('|')) - 2)
                table.style = 'Light Grid Accent 1'
                for r_idx, row_text in enumerate(rows):
                    if r_idx == 1 and set(row_text.replace('|', '').replace('-', '').strip()) == set():
                        continue
                    cells = [c.strip() for c in row_text.split('|')[1:-1]]
                    for c_idx, cell_text in enumerate(cells):
                        if r_idx == 0:
                            cell = table.rows[0].cells[c_idx]
                        else:
                            cell = table.rows[r_idx - 1].cells[c_idx]
                        cell.text = cell_text

        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            p = doc.add_paragraph()
            p.style = doc.styles['Normal']
            run = p.add_run('\n'.join(code_lines))
            run.font.size = Pt(9)
            run.font.name = 'Consolas'

        elif line.startswith('---'):
            doc.add_paragraph('─' * 40)

        elif line.startswith('*') and line.endswith('*'):
            doc.add_paragraph(line.removeprefix('*').removesuffix('*')).italic = True

        else:
            p = doc.add_paragraph(line)
            if line.startswith('**') and line.endswith('**'):
                p.clear()
                run = p.add_run(line.removeprefix('*').removesuffix('*'))
                run.bold = True

        i += 1

    doc.save(buf)


async def _export_docx(content: str, filename: str) -> FileResponse:
    buf = io.BytesIO()
    _md_to_docx(content, buf)
    buf.seek(0)
    docx_filename = filename.replace('.md', '.docx')
    tmp_path = OUTPUT_DIR / docx_filename
    async with aiofiles.open(tmp_path, 'wb') as f:
        await f.write(buf.read())
    return FileResponse(str(tmp_path), filename=docx_filename)


async def _export_pdf(content: str, filename: str) -> StreamingResponse:
    if not WEASYPRINT_AVAILABLE:
        raise HTTPException(501, "PDF экспорт недоступен: установите weasyprint")

    from io import BytesIO
    
    # Markdown -> HTML
    html_content = markdown.markdown(
        content,
        extensions=['tables', 'fenced_code', 'toc', 'attr_list']
    )
    
    # CSS для красивого PDF
    css = CSS(string='''
        @page {
            size: A4;
            margin: 2cm;
            @top-center { content: "Отчёт по аудиту ИТ-инфраструктуры"; font-size: 9pt; color: #666; }
            @bottom-center { content: counter(page); font-size: 9pt; color: #666; }
        }
        body {
            font-family: "DejaVu Sans", "Arial", sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #333;
        }
        h1, h2, h3, h4 {
            color: #1F3A5F;
            page-break-after: avoid;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 { font-size: 18pt; border-bottom: 2px solid #1F3A5F; padding-bottom: 4px; }
        h2 { font-size: 15pt; border-bottom: 1px solid #1F3A5F; padding-bottom: 3px; }
        h3 { font-size: 13pt; }
        h4 { font-size: 12pt; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            page-break-inside: auto;
        }
        tr { page-break-inside: avoid; page-break-after: auto; }
        th, td {
            border: 1px solid #ddd;
            padding: 6px 8px;
            font-size: 9pt;
        }
        th {
            background-color: #1F3A5F;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) td { background-color: #f5f5f5; }
        code {
            font-family: "DejaVu Sans Mono", "Consolas", monospace;
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 9pt;
            color: #CC0000;
        }
        pre {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 8.5pt;
            page-break-inside: avoid;
        }
        pre code { background: none; padding: 0; color: inherit; }
        blockquote {
            border-left: 4px solid #1F3A5F;
            padding-left: 12px;
            margin: 1em 0;
            color: #666;
            font-style: italic;
        }
        hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 1.5em 0;
        }
        p { margin: 0.5em 0; }
        ul, ol { margin: 0.5em 0; padding-left: 2em; }
        li { margin: 0.25em 0; }
        .toc { page-break-after: always; }
    ''')
    
    # Полный HTML документ
    full_html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Отчёт по аудиту</title>
</head>
<body>
{html_content}
</body>
</html>'''
    
    # Генерация PDF
    buffer = BytesIO()
    HTML(string=full_html).write_pdf(buffer, stylesheets=[css])
    buffer.seek(0)
    
    pdf_filename = filename.replace('.md', '.pdf')
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
    )


@router.get("/audit-history")
async def get_audit_history():
    return {"history": list_audit_history()}
