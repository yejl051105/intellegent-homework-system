import os

from fastapi import APIRouter, UploadFile, HTTPException

from backend.services.ocr_service import ocr, UPLOAD_FOLDER, save_upload

router = APIRouter()


@router.post("/upload")
async def upload(image: UploadFile):
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image file provided")

    filepath = save_upload(image, UPLOAD_FOLDER)
    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)

    try:
        result = ocr.predict(filepath)
        lines = []
        for item in result:
            lines.extend(item.get("rec_texts", []))
        return {"text": "\n".join(lines), "type": "ocr"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
