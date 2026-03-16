"""
Fetch and extract readable text content from URLs.

Strategy:
  1. trafilatura (primary — best general-purpose extractor)
  2. readability-lxml (fallback for complex layouts)
  3. If both fail or return too little text, include URL + title only

Skips login pages, search results, shopping carts, duplicates, and
other non-article URLs automatically.
"""

import re
from urllib.parse import urlparse

import trafilatura
from readability import Document
import urllib.request

# URL patterns that are unlikely to yield readable article content
SKIP_PATTERNS = re.compile(
    r"(google\.com/search|accounts\.google|instagram\.com|twitter\.com/i/|"
    r"x\.com/i/|/cart|/checkout|/login|/signin|/signup|/oauth|dropbox\.com/scl|"
    r"docs\.google\.com|slides\.google\.com|mail\.google|"
    r"\.png$|\.jpg$|\.jpeg$|\.gif$|\.pdf$|\.mp4$|\.mp3$)",
    re.IGNORECASE,
)

MIN_TEXT_LENGTH = 150  # chars — below this, we treat extraction as failed
MAX_TEXT_LENGTH = 2500  # chars — truncate to keep token usage reasonable

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _should_skip(url: str) -> bool:
    return bool(SKIP_PATTERNS.search(url))


def _fetch_html(url: str, timeout: int = 10) -> str | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _extract_with_trafilatura(url: str) -> tuple[str, str]:
    """Returns (title, text). Uses trafilatura's built-in fetch."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "", ""
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False) or ""
        # trafilatura doesn't easily expose title separately; extract from metadata
        metadata = trafilatura.extract(downloaded, output_format="json", with_metadata=True)
        title = ""
        if metadata:
            import json
            try:
                meta = json.loads(metadata)
                title = meta.get("title", "")
            except Exception:
                pass
        return title, text
    except Exception:
        return "", ""


def _extract_with_readability(url: str) -> tuple[str, str]:
    """Returns (title, text). Falls back to readability-lxml."""
    html = _fetch_html(url)
    if not html:
        return "", ""
    try:
        doc = Document(html)
        title = doc.title() or ""
        # doc.summary() returns HTML; strip tags for plain text
        summary_html = doc.summary()
        text = re.sub(r"<[^>]+>", " ", summary_html)
        text = re.sub(r"\s+", " ", text).strip()
        return title, text
    except Exception:
        return "", ""


def fetch_content(items: list[dict]) -> list[dict]:
    """
    Input:  list of {title, url, source} dicts
    Output: same dicts with 'text' field added (may be empty string)

    Deduplicates by domain+path to avoid processing the same article twice.
    """
    seen_urls: set[str] = set()
    results = []

    for item in items:
        url = item.get("url", "")
        if not url:
            continue

        # Deduplicate
        normalized = url.rstrip("/").split("?")[0].split("#")[0]
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)

        result = dict(item)
        result.setdefault("title", "")
        result["text"] = ""

        if _should_skip(url):
            print(f"[content] Skipped: {url[:80]}")
            results.append(result)
            continue

        # Try trafilatura first
        title, text = _extract_with_trafilatura(url)

        # Fall back to readability
        if len(text) < MIN_TEXT_LENGTH:
            fb_title, fb_text = _extract_with_readability(url)
            if len(fb_text) > len(text):
                title, text = fb_title, fb_text

        if title and not result["title"]:
            result["title"] = title

        if len(text) >= MIN_TEXT_LENGTH:
            result["text"] = text[:MAX_TEXT_LENGTH]
            print(f"[content] OK ({len(text)} chars): {url[:70]}")
        else:
            print(f"[content] No content ({len(text)} chars): {url[:70]}")

        results.append(result)

    extracted = sum(1 for r in results if r.get("text"))
    print(f"[content] {extracted}/{len(results)} items had extractable content")
    return results


if __name__ == "__main__":
    test_urls = [
        {"title": "Test", "url": "https://every.to/chain-of-thought/compound-engineering-how-every-codes-with-agents", "source": "tab"},
    ]
    results = fetch_content(test_urls)
    for r in results:
        print(f"\n{r['title']}\n{r['url']}\n{r['text'][:200]}...")
