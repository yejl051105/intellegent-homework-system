import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader
from docx import Document


class CriteriaExtractionError(Exception):
    """Raised when an uploaded rubric cannot be converted to text."""


def _extract_pdf(filepath: str) -> str:
    try:
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        raise CriteriaExtractionError("PDF 评分标准读取失败，请检查文件是否损坏。") from exc


def _extract_docx(filepath: str) -> str:
    try:
        document = Document(filepath)
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        return "\n".join(paragraphs).strip()
    except Exception as exc:
        raise CriteriaExtractionError("DOCX 评分标准读取失败，请检查文件是否损坏。") from exc


def _extract_doc(filepath: str) -> str:
    converter = shutil.which("textutil")
    if not converter:
        raise CriteriaExtractionError("当前环境暂不支持读取 DOC 文件，请转换为 PDF 或 DOCX 后再上传。")
    try:
        result = subprocess.run(
            [converter, "-convert", "txt", "-stdout", filepath],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CriteriaExtractionError("DOC 评分标准读取失败，请转换为 PDF 或 DOCX 后再上传。") from exc
    return result.stdout.strip()


def extract_criteria_text(filepath: str) -> str:
    suffix = Path(filepath).suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf(filepath)
    elif suffix == ".docx":
        text = _extract_docx(filepath)
    elif suffix == ".doc":
        text = _extract_doc(filepath)
    else:
        raise CriteriaExtractionError("评分标准附件格式不受支持。")

    if not text:
        raise CriteriaExtractionError("没有从评分标准附件中提取到文字，请上传可复制文字的 PDF 或 Word 文件。")
    return text[:12000]
