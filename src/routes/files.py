from fastapi import APIRouter, UploadFile, File, HTTPException

from src.storage import list_files, save_upload, delete_file, clear_temp

router = APIRouter()


@router.get("/files")
async def get_files():
    return list_files()


@router.post("/upload/{category}")
async def upload_file(category: str, file: UploadFile = File(...)):
    try:
        filename = await save_upload(category, file)
        return {"status": "success", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ошибка загрузки: {e}")


@router.delete("/files/{category}/{filename}")
async def remove_file(category: str, filename: str):
    try:
        delete_file(category, filename)
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ошибка удаления: {e}")


@router.post("/clear-temp")
async def clear_temp_data():
    counts = clear_temp()
    return {"status": "success", "cleared": counts}
