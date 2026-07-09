import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db, seed_eol_to_inventories
from src.routes.ui import router as ui_router
from src.routes.files import router as files_router
from src.routes.chat import router as chat_router
from src.routes.report_routes import router as report_router

app = FastAPI(title="iqData Bot - Аудит ИТ-инфраструктуры")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ui_router)
app.include_router(files_router)
app.include_router(chat_router)
app.include_router(report_router)


@app.on_event("startup")
async def startup():
    init_db()
    seed_eol_to_inventories()


@app.get("/health")
async def health():
    return {"status": "ok", "message": "iqData Bot running"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)
