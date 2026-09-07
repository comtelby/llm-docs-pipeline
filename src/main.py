import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db, seed_eol_to_inventories
from src.routes.audit import router as audit_router
from src.routes.chat import router as chat_router
from src.routes.files import router as files_router
from src.routes.report_routes import router as report_router
from src.routes.ui import router as ui_router
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up iqData Bot...")
    print("LIFESPAN STARTUP STARTED", flush=True)
    try:
        init_db()
        logger.info("Database initialized successfully")
        print("Database initialized successfully", flush=True)
        seed_eol_to_inventories()
        logger.info("EOL data seeded")
        print("EOL data seeded", flush=True)
    except Exception as e:
        logger.error(f"Startup error: {e}")
        print(f"Startup error: {e}", flush=True)
        raise
    yield
    # Shutdown
    logger.info("Shutting down iqData Bot...")
    print("LIFESPAN SHUTDOWN", flush=True)


app = FastAPI(title="iqData Bot - Аудит ИТ-инфраструктуры", lifespan=lifespan)

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
app.include_router(audit_router, prefix="/api", tags=["audit"])


@app.get("/health")
async def health():
    return {"status": "ok", "message": "iqData Bot running"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)
