import os

from fastapi import APIRouter, HTTPException, UploadFile

from backend.exceptions.system import ThirdPartyServiceException
from backend.schemas.response import ApiResponse
from backend.services.ocr_service import (
    UPLOAD_FOLDER,
    extract_text_document,
    get_formula_pipeline,
    get_formula_recognizer,
    ocr,
    save_upload,
)
from backend.utils.response import success

router = APIRouter(tags=["recognition"])


@router.post("/upload", response_model=ApiResponse)
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
        return success(data={"text": "\n".join(lines), "type": "ocr"})
    except Exception as exc:
        raise ThirdPartyServiceException("OCR 服务调用失败。") from exc
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@router.post("/upload/formula", response_model=ApiResponse)
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
        return success(data={"text": "\n\n".join(formulas), "type": "formula"})
    except Exception as exc:
        raise ThirdPartyServiceException("公式识别服务调用失败。") from exc
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@router.post("/upload/combined", response_model=ApiResponse)
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
        text_document = extract_text_document(filepath)
        output_parts.extend(item["text"] for item in text_document["items"])

        return success(
            data={
                "text": "\n".join(output_parts),
                "type": "combined",
                "image": text_document["image"],
                "items": text_document["items"],
            }
        )
    except Exception as exc:
        raise ThirdPartyServiceException("组合识别服务调用失败。") from exc
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
