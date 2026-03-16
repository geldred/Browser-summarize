# Browser-summarize

A personal weekly digest app. Every Sunday it:
1. Reads your open Safari tabs (saved from iOS Shortcut → iCloud Drive)
2. Fetches your Gmail from the past 7 days
3. Fetches article content from all URLs
4. Asks Claude to summarize and rank everything
5. Emails you a clean HTML digest

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your values
```

Required variables:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `DIGEST_EMAIL_TO` | Gmail address to send digest to |
| `GMAIL_CREDENTIALS_PATH` | Path to Gmail OAuth2 credentials.json |
| `GMAIL_TOKEN_PATH` | Path where token.json will be saved |
| `ICLOUD_DRIVE_PATH` | Path to iCloud Drive WeeklyDigest folder |
| `ARCHIVE_PATH` | Where to save digest archives locally |

### 3. Set up Gmail OAuth2 (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → **APIs & Services** → Enable **Gmail API**
3. **Credentials** → Create **OAuth2 client ID** (Desktop app) → Download JSON
4. Save to the path in `GMAIL_CREDENTIALS_PATH`
5. Run the setup script:
   ```bash
   python setup/oauth_setup.py
   ```
   A browser window will open — authenticate and close it.

### 4. Set up iOS Shortcut

See [`shortcuts/SETUP.md`](shortcuts/SETUP.md) for step-by-step instructions to
build a Shortcut that auto-exports your Safari tabs to iCloud Drive weekly.

### 5. Schedule with macOS Launchd

```bash
# Edit the plist to replace YOUR_USERNAME and paths
cp setup/com.user.weeklydigest.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.weeklydigest.plist

# Test it runs immediately
launchctl start com.user.weeklydigest
```

---

## Usage

```bash
# Full run (fetch tabs + email, send digest)
python digest.py

# Preview without sending email
python digest.py --dry-run

# Tabs only (skip Gmail)
python digest.py --tabs-only

# Emails only (skip tabs)
python digest.py --emails-only
```

---

## Project Structure

```
Browser-summarize/
├── digest.py              # Main entry point / orchestrator
├── summarizer.py          # Claude API: batch summarize + rank
├── formatter.py           # HTML + plain-text email rendering
├── sender.py              # Gmail SMTP delivery
├── sources/
│   ├── tabs.py            # Read tabs JSON from iCloud Drive
│   ├── gmail.py           # Fetch emails via Gmail API
│   └── content.py         # Fetch URL content (trafilatura)
├── setup/
│   ├── oauth_setup.py     # One-time Gmail OAuth setup
│   └── com.user.weeklydigest.plist  # macOS Launchd schedule
└── shortcuts/
    └── SETUP.md           # iOS Shortcut build instructions
```
