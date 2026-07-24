import os

import os

from fastapi import APIRouter, UploadFile, HTTPException

from backend.services.ocr_service import get_formula_recognizer, UPLOAD_FOLDER, save_upload

router = APIRouter()


@router.post("/upload/formula")
async def upload_formula(image: UploadFile):
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image file provided")

    filepath = save_upload(image, UPLOAD_FOLDER)
    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)

    try:
        recognizer = get_formula_recognizer()
        result = recognizer.predict(input=filepath, batch_size=1)
        formulas = []
        for res in result:
            data = res.json
            formulas.append(data.get("rec_formula", ""))
        return {"text": "\n\n".join(formulas), "type": "formula"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
