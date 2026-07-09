from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.config import TEMPLATES_DIR
from jinja2 import Environment, FileSystemLoader, select_autoescape

router = APIRouter()

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0
)


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        template = env.get_template("index.html")
        return template.render({"request": request, "title": "iqData Bot - Аудит ИТ-инфраструктуры"})
    except Exception:
        return HTMLResponse("<h1>Ошибка загрузки шаблона</h1>", status_code=500)


@router.get("/reports-page", response_class=HTMLResponse)
async def reports_page(request: Request):
    try:
        template = env.get_template("reports.html")
        return template.render({"request": request, "title": "Просмотр отчётов"})
    except Exception:
        return HTMLResponse("<h2>Отчёты</h2><a href='/'>На главную</a>")
