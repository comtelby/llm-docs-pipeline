from fastapi import APIRouter, HTTPException, UploadFile

from src.storage import clear_temp, delete_file, list_files, save_upload

router = APIRouter()


@router.get("/files")
async def get_files():
    return list_files()


@router.post("/upload/{category}")
async def upload_file(category: str, file: UploadFile):
    try:
        filename = await save_upload(category, file)
        return {"status": "success", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Ошибка загрузки: {e}")


@router.delete("/files/{category}/{filename}")
async def remove_file(category: str, filename: str):
    try:
        delete_file(category, filename)
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Ошибка удаления: {e}")


@router.post("/clear-temp")
async def clear_temp_data():
    counts = clear_temp()
    return {"status": "success", "cleared": counts}
