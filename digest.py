#!/usr/bin/env python3
"""
Weekly Digest — main entry point.

Orchestrates the full pipeline:
  1. Load tabs from iCloud Drive JSON
  2. Fetch Gmail emails from the past 7 days
  3. Collect all URLs and fetch their content
  4. Summarize and rank with Claude
  5. Render HTML + plain-text digest
  6. Send email and archive locally

Usage:
    python digest.py                     # full run
    python digest.py --dry-run           # skip sending email, save to /tmp
    python digest.py --tabs-only         # skip email sources
    python digest.py --emails-only       # skip tab sources
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_archive_path() -> Path:
    raw = os.getenv("ARCHIVE_PATH", "~/WeeklyDigest/archive")
    p = Path(raw).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def run(dry_run: bool = False, tabs_only: bool = False, emails_only: bool = False) -> None:
    from sources.tabs import load_tabs
    from sources.gmail import fetch_emails
    from sources.content import fetch_content
    from summarizer import summarize_and_rank
    from formatter import render_html, render_text
    from sender import send_digest

    week_label = datetime.now().strftime("Week of %B %-d, %Y")
    print(f"\n{'='*60}")
    print(f"Weekly Digest — {week_label}")
    print(f"{'='*60}\n")

    # ── Step 1: Collect items ──────────────────────────────────────
    content_items: list[dict] = []

    if not emails_only:
        tabs = load_tabs()
        for tab in tabs:
            content_items.append({
                "title": tab.get("title", ""),
                "url": tab["url"],
                "source": "tab",
            })
        print(f"[digest] Tabs loaded: {len(tabs)}")

    email_urls: list[dict] = []
    if not tabs_only:
        try:
            emails = fetch_emails(days_back=7)
        except Exception as e:
            print(f"[digest] Gmail fetch failed: {e}")
            emails = []

        for email in emails:
            # Add each email's extracted URLs as content items
            for url in email.get("urls", []):
                email_urls.append({
                    "title": email.get("subject", ""),
                    "url": url,
                    "source": "email",
                })

            # Also add the email itself as a summarizable item (no URL fetch)
            snippet = email.get("snippet", "")
            if snippet:
                content_items.append({
                    "title": email.get("subject", "(no subject)"),
                    "url": f"gmail:{email.get('subject','').replace(' ','+')}",
                    "source": "email",
                    "text": f"From: {email.get('sender','')}\n\n{snippet}",
                })

        content_items.extend(email_urls)
        print(f"[digest] Email items: {len(emails)} emails → {len(email_urls)} URLs + {len(emails)} snippets")

    if not content_items:
        print("[digest] No items to process. Exiting.")
        return

    print(f"[digest] Total items before content fetch: {len(content_items)}\n")

    # ── Step 2: Fetch page content ─────────────────────────────────
    # Only fetch URL content for items that don't already have text
    to_fetch = [i for i in content_items if not i.get("text") and not i["url"].startswith("gmail:")]
    already_have_text = [i for i in content_items if i.get("text") or i["url"].startswith("gmail:")]

    print(f"[digest] Fetching content for {len(to_fetch)} URLs...")
    fetched = fetch_content(to_fetch)
    all_items = already_have_text + fetched

    print(f"\n[digest] Items ready for summarization: {len(all_items)}\n")

    # ── Step 3: Summarize & rank ───────────────────────────────────
    ranked = summarize_and_rank(all_items)

    # ── Step 4: Render ─────────────────────────────────────────────
    html_body = render_html(ranked, week_label=week_label)
    text_body = render_text(ranked, week_label=week_label)

    # ── Step 5: Archive ────────────────────────────────────────────
    archive_dir = _get_archive_path()
    date_str = datetime.now().strftime("%Y-%m-%d")
    html_path = archive_dir / f"{date_str}.html"
    text_path = archive_dir / f"{date_str}.txt"

    html_path.write_text(html_body)
    text_path.write_text(text_body)
    print(f"\n[digest] Archived to {archive_dir}/")

    # ── Step 6: Send ───────────────────────────────────────────────
    if dry_run:
        preview_path = Path("/tmp/digest_preview.html")
        preview_path.write_text(html_body)
        print(f"[digest] Dry run — preview saved to {preview_path}")
        print("\n" + text_body[:1500])
    else:
        try:
            send_digest(html_body, text_body, week_label=week_label)
        except Exception as e:
            print(f"[digest] Email send failed: {e}")
            print(f"[digest] Digest still archived at {html_path}")

    print(f"\n[digest] Done. {len(ranked)} items ranked.")


def main():
    parser = argparse.ArgumentParser(description="Generate and send your weekly reading digest")
    parser.add_argument("--dry-run", action="store_true", help="Skip sending email, save preview to /tmp")
    parser.add_argument("--tabs-only", action="store_true", help="Only process browser tabs (skip Gmail)")
    parser.add_argument("--emails-only", action="store_true", help="Only process emails (skip tabs)")
    args = parser.parse_args()

    if args.tabs_only and args.emails_only:
        print("Error: --tabs-only and --emails-only are mutually exclusive")
        sys.exit(1)

    run(dry_run=args.dry_run, tabs_only=args.tabs_only, emails_only=args.emails_only)


if __name__ == "__main__":
    main()
