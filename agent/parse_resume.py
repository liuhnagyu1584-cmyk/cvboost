import os


async def parse_resume(file_path: str) -> str:
    """Parse PDF/Word resume file and return extracted text."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext in (".docx", ".doc"):
        from docx import Document

        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    return f"[错误] 不支持的文件格式：{ext}。支持：.pdf / .docx / .doc"
