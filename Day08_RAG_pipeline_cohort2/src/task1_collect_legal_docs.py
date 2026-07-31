"""
Task 1 - Collect legal documents about drugs and controlled substances.

Goal:
    Download at least 3 PDF/DOC/DOCX legal documents into:
        data/landing/legal/

How to use:
    1. Find direct download links for official PDF/DOC/DOCX files.
    2. Put those links in LEGAL_DOCUMENTS below.
    3. Run:
        python src/task1_collect_legal_docs.py
    4. Check:
        pytest tests/test_individual.py::TestTask1 -v

Important:
    Use direct file links, not normal article/detail pages.

Good direct URL examples usually end with:
    .pdf
    .doc
    .docx

Bad URL examples:
    https://example.com/van-ban/some-law.aspx
    This is usually an HTML page, not a downloadable document file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MIN_FILE_SIZE_BYTES = 1024


@dataclass(frozen=True)
class LegalDocument:
    title: str
    url: str
    filename: str


# Replace the example URLs below with direct PDF/DOC/DOCX download links.
# Suggested documents:
# - Luat Phong, chong ma tuy 2021 - 73/2021/QH15
# - Nghi dinh 105/2021/ND-CP
# - Bo luat Hinh su 2015, sua doi 2017 - drug crime chapter
# - Nghi dinh 57/2022/ND-CP - controlled substances list
LEGAL_DOCUMENTS: list[LegalDocument] = [
    LegalDocument(
        title="Luat Phong, chong ma tuy 2021",
        url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/01/73luat.pdf",
        filename="luat-phong-chong-ma-tuy-2021.pdf",
    ),
    LegalDocument(
        title="Nghi dinh 105/2021/ND-CP",
        url="https://cscnmt.khanhhoa.gov.vn/laws/detail/Nghi-dinh-Quy-dinh-chi-tiet-va-huong-dan-thi-hanh-mot-so-dieu-cua-Luat-Phong-Chong-ma-tuy-24/?download=1&id=0",
        filename="nghi-dinh-105-2021.pdf",
    ),
    LegalDocument(
        title="Bo luat Hinh su 2015 sua doi 2017",
        url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/9/135-vbhn-vpqh.pdf",
        filename="bo-luat-hinh-su-2015-sua-doi-2017.pdf",
    ),
]


def setup_directory() -> None:
    """Create data/landing/legal/ if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def validate_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"{filename!r} must end with one of: {allowed}")


def looks_like_placeholder(url: str) -> bool:
    return not url or url.startswith("PASTE_")


def download_file(url: str, filename: str) -> Path:
    """
    Download one legal document and save it under data/landing/legal/.

    The file is downloaded with streaming so large PDF/DOCX files do not need
    to be held fully in memory.
    """
    validate_filename(filename)

    filepath = DATA_DIR / filename
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    with requests.get(url, headers=headers, stream=True, timeout=60, verify=False) as response:
        response.raise_for_status()
        with filepath.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)

    validate_download(filepath)
    return filepath


def validate_download(filepath: Path) -> None:
    """Make sure the downloaded file is usable for this task."""
    if not filepath.exists():
        raise FileNotFoundError(f"Download failed, file not found: {filepath}")

    if filepath.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid extension: {filepath.name}")

    file_size = filepath.stat().st_size
    if file_size <= MIN_FILE_SIZE_BYTES:
        raise ValueError(
            f"{filepath.name} is too small ({file_size} bytes). "
            "The URL may not be a real document file."
        )

    if filepath.suffix.lower() == ".pdf":
        first_bytes = filepath.read_bytes()[:5]
        if first_bytes != b"%PDF-":
            raise ValueError(
                f"{filepath.name} does not look like a real PDF. "
                "You may have downloaded an HTML page instead of the PDF file."
            )

    if filepath.suffix.lower() == ".docx":
        first_bytes = filepath.read_bytes()[:4]
        if first_bytes != b"PK\x03\x04":
            raise ValueError(
                f"{filepath.name} does not look like a real DOCX file. "
                "DOCX files are ZIP-based and should start with PK bytes. "
                "Use a .doc filename if the source is an older Word document."
            )

    if filepath.suffix.lower() == ".doc":
        first_bytes = filepath.read_bytes()[:4]
        if first_bytes != b"\xd0\xcf\x11\xe0":
            raise ValueError(
                f"{filepath.name} does not look like a real DOC file. "
                "You may have downloaded an HTML page instead of the document."
            )


def download_all(documents: list[LegalDocument] = LEGAL_DOCUMENTS) -> list[Path]:
    """Download all configured legal documents."""
    setup_directory()
    downloaded: list[Path] = []

    for index, doc in enumerate(documents, start=1):
        print(f"\n[{index}/{len(documents)}] {doc.title}")

        if looks_like_placeholder(doc.url):
            print("Skipped: fill in a direct PDF/DOC/DOCX URL first.")
            continue

        parsed_url = urlparse(doc.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            print(f"Skipped: invalid URL: {doc.url}")
            continue

        try:
            filepath = download_file(doc.url, doc.filename)
        except Exception as exc:
            print(f"Failed: {exc}")
            continue

        downloaded.append(filepath)
        print(f"Saved: {filepath} ({filepath.stat().st_size:,} bytes)")

    return downloaded


def count_valid_legal_files() -> int:
    """Count existing PDF/DOC/DOCX files that satisfy the Task 1 size check."""
    if not DATA_DIR.exists():
        return 0

    valid_files = [
        path
        for path in DATA_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in ALLOWED_EXTENSIONS
        and path.stat().st_size > MIN_FILE_SIZE_BYTES
    ]
    return len(valid_files)


def main() -> None:
    downloaded = download_all()
    valid_count = count_valid_legal_files()

    print("\nSummary")
    print(f"Downloaded in this run: {len(downloaded)}")
    print(f"Valid legal files total: {valid_count}")

    if valid_count >= 3:
        print("Task 1 looks ready. Run: pytest tests/test_individual.py::TestTask1 -v")
    else:
        print("Task 1 still needs at least 3 valid PDF/DOC/DOCX files.")


if __name__ == "__main__":
    main()
