"""
Batch summarize and rank all content items using Claude.

Sends all items (tabs + email URLs) in a single API call and returns
a ranked list with summaries, scores, and categories.
"""

import json
import os
from datetime import datetime

import anthropic

MODEL = "claude-opus-4-6"
MAX_ITEMS_PER_BATCH = 60  # keeps prompt manageable


def _build_prompt(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        title = item.get("title") or "(no title)"
        url = item.get("url", "")
        source = item.get("source", "tab")
        text = item.get("text", "").strip()

        lines.append(f"--- Item {i} ---")
        lines.append(f"Title: {title}")
        lines.append(f"URL: {url}")
        lines.append(f"Source: {source}")
        if text:
            lines.append(f"Content excerpt: {text[:1200]}")
        lines.append("")

    items_text = "\n".join(lines)

    return f"""You are curating a personal weekly reading digest. Below are {len(items)} items from this week's open browser tabs and emails.

For each item, provide:
- A 1–2 sentence summary (skip if content is a shopping page, login page, or search result — mark those as "skip")
- A relevance/interest score from 1–10 (10 = must-read, 1 = trivial/noise)
- A category from: technology, productivity, culture, finance, health, personal, news, shopping, other

Rules:
- Score items higher if they are substantive articles, essays, newsletters, or important emails
- Score lower for routine/transactional emails, shopping pages, search results
- Items marked "skip" should still appear in the output but with score 1–2

Return ONLY a valid JSON array (no markdown, no commentary before or after), sorted by score descending:
[
  {{
    "rank": 1,
    "title": "...",
    "url": "...",
    "source": "tab" or "email",
    "summary": "...",
    "score": 9,
    "category": "technology"
  }},
  ...
]

Items to process:

{items_text}"""


def summarize_and_rank(items: list[dict]) -> list[dict]:
    """
    Takes a list of content items and returns them ranked with summaries.
    Each item should have: title, url, source, text (optional).
    """
    if not items:
        return []

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Process in batches if we have many items
    all_results = []
    for batch_start in range(0, len(items), MAX_ITEMS_PER_BATCH):
        batch = items[batch_start : batch_start + MAX_ITEMS_PER_BATCH]
        batch_num = batch_start // MAX_ITEMS_PER_BATCH + 1
        total_batches = (len(items) + MAX_ITEMS_PER_BATCH - 1) // MAX_ITEMS_PER_BATCH

        print(f"[summarizer] Calling Claude for batch {batch_num}/{total_batches} ({len(batch)} items)...")

        prompt = _build_prompt(batch)

        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()

        raw_text = next(
            (b.text for b in response.content if b.type == "text"), ""
        )

        try:
            ranked = json.loads(raw_text)
            if not isinstance(ranked, list):
                raise ValueError("Response was not a JSON array")
            all_results.extend(ranked)
            print(f"[summarizer] Batch {batch_num} complete: {len(ranked)} items ranked")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[summarizer] JSON parse error in batch {batch_num}: {e}")
            print(f"[summarizer] Raw response (first 500 chars): {raw_text[:500]}")
            # Fall back: include items without summaries
            for item in batch:
                all_results.append({
                    "rank": 99,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", "tab"),
                    "summary": "(summary unavailable)",
                    "score": 5,
                    "category": "other",
                })

    # Re-sort globally by score after merging batches
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    for i, item in enumerate(all_results, 1):
        item["rank"] = i

    print(f"[summarizer] Total: {len(all_results)} items ranked")
    return all_results


if __name__ == "__main__":
    # Quick test with mock data
    mock_items = [
        {
            "title": "How Every codes with AI agents",
            "url": "https://every.to/chain-of-thought/compound-engineering",
            "source": "tab",
            "text": "Compound engineering is a methodology for building software with AI agents...",
        },
        {
            "title": "Your Amazon order has shipped",
            "url": "https://amazon.com/orders/123",
            "source": "email",
            "text": "Your order #123 has been shipped and will arrive by Friday.",
        },
    ]
    results = summarize_and_rank(mock_items)
    for r in results:
        print(f"#{r['rank']} [{r['score']}/10] {r['title']}")
        print(f"   {r['summary']}")
        print()
