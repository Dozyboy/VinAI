"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install "markitdown[pdf]"

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _build_pdf_fallback_markdown(filepath):
    """Build markdown metadata when a PDF has no extractable text layer."""
    page_count = "unknown"
    try:
        import pdfplumber

        with pdfplumber.open(filepath) as pdf:
            page_count = len(pdf.pages)
    except Exception:
        pass

    return (
        f"# {filepath.stem}\n\n"
        f"**Source file:** `{filepath.name}`\n\n"
        f"**File type:** PDF\n\n"
        f"**File size:** {filepath.stat().st_size:,} bytes\n\n"
        f"**Pages:** {page_count}\n\n"
        "## Conversion note\n\n"
        "MarkItDown ran successfully, but it did not find an extractable text layer "
        "inside this PDF. This usually means the document is a scanned image PDF or "
        "has a layout that pdfminer/pdfplumber cannot read as text.\n\n"
        "To extract the full legal text from this document, run an OCR step first "
        "or replace the source with a searchable PDF/DOCX version, then run this "
        "conversion task again.\n"
    )


def _build_office_fallback_markdown(filepath, error):
    """Build markdown metadata when MarkItDown cannot parse an Office file."""
    return (
        f"# {filepath.stem}\n\n"
        f"**Source file:** `{filepath.name}`\n\n"
        f"**File type:** {filepath.suffix.upper().lstrip('.')}\n\n"
        f"**File size:** {filepath.stat().st_size:,} bytes\n\n"
        "## Conversion note\n\n"
        "MarkItDown could not extract text from this Microsoft Office document. "
        "This often happens when a file is an older binary `.doc` document, or "
        "when the downloaded file extension does not match the real file format.\n\n"
        f"**Converter error:** `{type(error).__name__}: {error}`\n\n"
        "To extract the full legal text, open the source document in Microsoft "
        "Word or LibreOffice, save/export it as a modern `.docx` or searchable "
        "PDF, then run this conversion task again.\n"
    )


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            try:
                result = md.convert(str(filepath))
            except Exception as exc:
                if filepath.suffix.lower() == ".pdf" and "MissingDependencyException" in str(exc):
                    raise RuntimeError(
                        "MarkItDown chưa được cài kèm dependency để đọc PDF. "
                        'Chạy: pip install "markitdown[pdf]"'
                    ) from exc
                if filepath.suffix.lower() in (".docx", ".doc"):
                    print("  Warning: Office document could not be converted; writing metadata fallback")
                    text_content = _build_office_fallback_markdown(filepath, exc)
                    output_path = output_dir / f"{filepath.stem}.md"
                    output_path.write_text(text_content, encoding="utf-8")
                    print(f"  Saved: {output_path}")
                    continue
                raise
            text_content = result.text_content.strip()
            if not text_content and filepath.suffix.lower() == ".pdf":
                print("  Warning: no extractable PDF text; writing metadata fallback")
                text_content = _build_pdf_fallback_markdown(filepath)
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(text_content, encoding="utf-8")
            print(f"  Saved: {output_path}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            output_path = output_dir / f"{filepath.stem}.md"

            header = f"# {data.get('title', 'Unknown')}\n\n"
            header += f"**Source:** {data.get('url', 'N/A')}\n"
            header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"

            content = header + data.get("content_markdown", "")
            output_path.write_text(content, encoding="utf-8")
            print(f"  Saved: {output_path}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\nDone! Output tai:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
