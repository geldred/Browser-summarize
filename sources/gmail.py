"""
Fetch emails from the past 7 days via Gmail API (OAuth2).
Returns a list of dicts: {subject, sender, snippet, urls, date}

Run setup/oauth_setup.py once to generate token.json before using this.
"""

import base64
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

URL_RE = re.compile(r'https?://[^\s<>"\')\]]+')
# Skip these URL patterns — they're noise, not content
SKIP_URL_PATTERNS = re.compile(
    r"(unsubscribe|click\.|track\.|open\.|mail\.google|accounts\.google|"
    r"fonts\.googleapis|cdn\.|pixel\.|beacon\.|utm_|/r/|/t/)",
    re.IGNORECASE,
)


def _creds_path() -> Path:
    return Path(os.getenv("GMAIL_CREDENTIALS_PATH", "~/.config/weekly-digest/credentials.json")).expanduser()


def _token_path() -> Path:
    return Path(os.getenv("GMAIL_TOKEN_PATH", "~/.config/weekly-digest/token.json")).expanduser()


def _get_credentials() -> Credentials:
    token_path = _token_path()
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_creds_path()), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return creds


def _decode_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    # Recurse into multipart parts, preferring text/plain
    parts = payload.get("parts", [])
    for part in parts:
        text = _decode_body(part)
        if text:
            return text

    return ""


def _extract_urls(text: str) -> list[str]:
    urls = URL_RE.findall(text)
    seen = set()
    result = []
    for url in urls:
        url = url.rstrip(".,;)")
        if url in seen:
            continue
        seen.add(url)
        if not SKIP_URL_PATTERNS.search(url):
            result.append(url)
    return result


def fetch_emails(days_back: int = 7, max_results: int = 100) -> list[dict]:
    """
    Return emails from the past `days_back` days, excluding sent/spam/trash.
    Each item: {subject, sender, snippet, urls, date}
    """
    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query = f"after:{after_date} -in:sent -in:spam -in:trash"

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    print(f"[gmail] Found {len(messages)} emails to process")

    emails = []
    for msg_ref in messages:
        try:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()
        except Exception as e:
            print(f"[gmail] Error fetching message {msg_ref['id']}: {e}")
            continue

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "")
        snippet = msg.get("snippet", "")
        date_str = headers.get("Date", "")

        body = _decode_body(msg.get("payload", {}))
        urls = _extract_urls(body or snippet)

        emails.append({
            "subject": subject,
            "sender": sender,
            "snippet": snippet[:300],
            "urls": urls[:10],  # cap per-email URL count
            "date": date_str,
        })

    print(f"[gmail] Processed {len(emails)} emails, extracted {sum(len(e['urls']) for e in emails)} URLs")
    return emails


if __name__ == "__main__":
    emails = fetch_emails()
    for e in emails[:5]:
        print(f"  [{e['date'][:16]}] {e['sender'][:30]} — {e['subject'][:60]}")
        print(f"    URLs: {len(e['urls'])}")
