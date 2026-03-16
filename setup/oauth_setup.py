"""
One-time Gmail OAuth2 setup script.

Run this once to generate token.json before running digest.py.

Steps:
1. Go to https://console.cloud.google.com/
2. Create a project → Enable Gmail API → Create OAuth2 credentials (Desktop app)
3. Download credentials JSON → save to path in GMAIL_CREDENTIALS_PATH (.env)
4. Run: python setup/oauth_setup.py
5. Authenticate in the browser window that opens
6. token.json will be saved to GMAIL_TOKEN_PATH

After this, digest.py will refresh the token automatically.
"""

import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    creds_path = Path(os.getenv("GMAIL_CREDENTIALS_PATH", "~/.config/weekly-digest/credentials.json")).expanduser()
    token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "~/.config/weekly-digest/token.json")).expanduser()

    if not creds_path.exists():
        print(f"ERROR: credentials.json not found at {creds_path}")
        print()
        print("To fix:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create project → APIs & Services → Enable Gmail API")
        print("  3. Credentials → Create OAuth2 client (Desktop app) → Download JSON")
        print(f"  4. Save it to: {creds_path}")
        sys.exit(1)

    print(f"Using credentials: {creds_path}")
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Token saved to: {token_path}")
    print("Setup complete. You can now run: python digest.py")


if __name__ == "__main__":
    main()
