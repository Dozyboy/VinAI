"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Điền danh sách URL bài báo cần crawl
ARTICLE_URLS = [
    "https://vnexpress.net/ma-tuy-trong-loi-song-showbiz-5074606.html",
    "https://tuoitre.vn/nghe-si-nguoi-noi-tieng-dinh-ma-tuy-nguy-co-lech-chuan-nhan-thuc-voi-gioi-tre-20260612175906838.htm",
    "https://baochinhphu.vn/khoi-to-le-anh-nhat-ca-si-miu-le-ve-hanh-vi-to-chuc-su-dung-trai-phep-chat-ma-tuy-102260516224626903.htm",
    "https://pcmatuy.bocongan.gov.vn/Tin-t%E1%BB%A9c-s%E1%BB%B1-ki%E1%BB%87n/articleType/ArticleView/articleId/2019/ca-s-chi-dn-v-anh-rut-r-bn-nhu-t-ma-ty-v-s-dng",
    "https://tienphong.vn/nghe-si-dinh-ma-tuy-khoang-trong-sau-nhung-cu-truot-nga-post1845503.tpo"

    # Ví dụ:
    # "https://vnexpress.net/...",
    # "https://tuoitre.vn/...",
    # "https://thanhnien.vn/...",
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        metadata = getattr(result, "metadata", {}) or {}

        return {
            "url": url,
            "title": metadata.get("title", "Unknown"),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": getattr(result, "markdown", "") or "",
        }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
