"""
Read the most recent Safari tabs JSON file from iCloud Drive.

The iOS Shortcut saves a file like tabs_YYYY-MM-DD.json to:
  iCloud Drive / WeeklyDigest / tabs_YYYY-MM-DD.json

Each file contains a JSON array: [{"title": "...", "url": "..."}, ...]
"""

import json
import os
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path


def get_icloud_path() -> Path:
    raw = os.getenv("ICLOUD_DRIVE_PATH", "~/Library/Mobile Documents/com~apple~CloudDocs/WeeklyDigest")
    return Path(raw).expanduser()


def load_tabs(max_age_days: int = 7) -> list[dict]:
    """
    Return the list of tabs from the most recent tabs_*.json file,
    provided it was created within max_age_days. Returns [] if none found.
    """
    folder = get_icloud_path()
    if not folder.exists():
        print(f"[tabs] iCloud folder not found: {folder}")
        return []

    pattern = str(folder / "tabs_*.json")
    files = sorted(glob(pattern), reverse=True)  # newest first by filename date

    cutoff = datetime.now() - timedelta(days=max_age_days)

    for path in files:
        # Extract date from filename: tabs_YYYY-MM-DD.json
        name = Path(path).stem  # "tabs_2026-03-16"
        try:
            file_date = datetime.strptime(name, "tabs_%Y-%m-%d")
        except ValueError:
            continue

        if file_date < cutoff:
            break  # files are sorted newest-first; stop once past window

        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, list):
                tabs = [t for t in data if isinstance(t, dict) and t.get("url")]
                print(f"[tabs] Loaded {len(tabs)} tabs from {Path(path).name}")
                return tabs
        except (json.JSONDecodeError, OSError) as e:
            print(f"[tabs] Error reading {path}: {e}")

    print("[tabs] No recent tabs file found.")
    return []


if __name__ == "__main__":
    tabs = load_tabs()
    for t in tabs[:5]:
        print(f"  {t.get('title', '(no title)')} — {t['url']}")
