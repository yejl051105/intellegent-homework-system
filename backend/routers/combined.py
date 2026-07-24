import os
from PIL import Image

import os

from fastapi import APIRouter, UploadFile, HTTPException

from backend.services.ocr_service import (
    get_formula_pipeline,
    UPLOAD_FOLDER,
    save_upload,
    crop_image,
    ocr_region,
)

router = APIRouter()


@router.post("/upload/combined")
async def upload_combined(image: UploadFile):
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image file provided")

    filepath = save_upload(image, UPLOAD_FOLDER)
    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)

    try:
        pipe = get_formula_pipeline()
        pipeline_result = pipe.predict(input=filepath, use_layout_detection=True)
        img = Image.open(filepath)

        output_parts = []

        for res in pipeline_result:
            data = res.json["res"]
            layout = data.get("layout_det_res", {})
            formula_list = data.get("formula_res_list", [])

            formula_by_id = {}
            for f_res in formula_list:
                rid = f_res.get("formula_region_id")
                formula_by_id[rid] = f_res.get("rec_formula", "")

            for box in layout.get("boxes", []):
                label = box.get("label", "")
                coord = box.get("coordinate", [])
                region_id = box.get("id")

                if label == "formula":
                    latex = formula_by_id.get(region_id, "")
                    if latex:
                        output_parts.append("[公式] " + latex)
                elif label in ("text", "paragraph_title", "document_title"):
                    region_img = crop_image(img, coord)
                    text = ocr_region(region_img, filepath)
                    if text.strip():
                        output_parts.append(text)

        return {"text": "\n".join(output_parts), "type": "combined"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
