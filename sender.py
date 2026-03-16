"""
Send the weekly digest email via Gmail SMTP using OAuth2.

Reuses the same OAuth2 credentials as the Gmail API reader.
"""

import base64
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://mail.google.com/",  # needed for SMTP send
]


def _get_credentials() -> Credentials:
    token_path = Path(
        os.getenv("GMAIL_TOKEN_PATH", "~/.config/weekly-digest/token.json")
    ).expanduser()
    creds_path = Path(
        os.getenv("GMAIL_CREDENTIALS_PATH", "~/.config/weekly-digest/credentials.json")
    ).expanduser()

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())

    if not creds or not creds.valid:
        raise RuntimeError(
            f"No valid Gmail credentials found at {token_path}.\n"
            "Run: python setup/oauth_setup.py"
        )

    return creds


def _oauth2_string(user: str, access_token: str) -> str:
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode()).decode()


def send_digest(html_body: str, text_body: str, week_label: str = None) -> None:
    """Send the digest email to DIGEST_EMAIL_TO."""
    to_addr = os.getenv("DIGEST_EMAIL_TO")
    if not to_addr:
        raise ValueError("DIGEST_EMAIL_TO environment variable not set")

    if week_label is None:
        week_label = datetime.now().strftime("Week of %B %-d, %Y")

    subject = f"Weekly Digest — {week_label}"

    creds = _get_credentials()
    access_token = creds.token

    # Use the same address as the authenticated account for From
    from_addr = to_addr  # sending to/from yourself

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    print(f"[sender] Connecting to {SMTP_HOST}:{SMTP_PORT}...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        auth_string = _oauth2_string(from_addr, access_token)
        smtp.docmd("AUTH", f"XOAUTH2 {auth_string}")
        smtp.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"[sender] Digest sent to {to_addr}")


if __name__ == "__main__":
    # Quick test — sends a minimal test email
    send_digest(
        html_body="<h1>Test digest</h1><p>If you see this, sending works!</p>",
        text_body="Test digest\n\nIf you see this, sending works!",
        week_label="Test",
    )
