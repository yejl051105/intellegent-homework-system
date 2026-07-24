import os

from fastapi import APIRouter, UploadFile, HTTPException

from backend.services.ocr_service import (
    get_formula_pipeline,
    UPLOAD_FOLDER,
    save_upload,
    extract_text_document,
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
                region_id = box.get("id")

                if label == "formula":
                    latex = formula_by_id.get(region_id, "")
                    if latex:
                        output_parts.append("[公式] " + latex)
        # Text OCR always runs once on the complete original file. The formula
        # pipeline may provide formula text separately, but never feeds a crop
        # into PaddleOCR.
        text_document = extract_text_document(filepath)
        output_parts.extend(item["text"] for item in text_document["items"])

        return {
            "text": "\n".join(output_parts),
            "type": "combined",
            "image": text_document["image"],
            "items": text_document["items"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
