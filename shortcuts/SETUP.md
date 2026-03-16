# iOS Shortcut Setup — Safari Tab Exporter

This Shortcut runs weekly on your iPhone, grabs all open Safari tabs,
and saves them as a JSON file to iCloud Drive. The Mac script reads that
file each Sunday when generating your digest.

---

## Requirements

- iPhone running **iOS 18.4 or later** (adds the "Find Tabs" action)
- iCloud Drive enabled

---

## Step-by-Step: Build the Shortcut

### 1. Open the Shortcuts app → tap **+** to create a new shortcut

### 2. Add these actions in order:

**Action 1 — Get current date**
- Search for: `Format Date`
- Date: `Current Date`
- Format: `Custom` → enter: `yyyy-MM-dd`
- Store result in variable: `TodayDate`

**Action 2 — Find all open Safari tabs**
- Search for: `Find Tabs`
- This returns all tabs across all tab groups

**Action 3 — Build a JSON array**
- Search for: `Repeat with each item`
- Set the input to: `Tabs` (from step 2)
- Inside the repeat loop, add:
  - Search for: `Get Details of Safari Tab`
  - Detail: `Title` → store as `TabTitle`
  - Add another `Get Details of Safari Tab`
  - Detail: `URL` → store as `TabURL`
  - Add `Dictionary` action with:
    - Key `title` → Value: `TabTitle` (variable)
    - Key `url` → Value: `TabURL` (variable)
  - Add `Add to Variable` → variable name: `TabsList`

**Action 4 — Convert to JSON text**
- After the repeat loop, add: `Get JSON from Input`
- Input: `TabsList` (variable)

**Action 5 — Save to iCloud Drive**
- Search for: `Save File`
- File: the JSON from step 4
- Destination: `iCloud Drive` → navigate to or create folder `WeeklyDigest`
- File name: `tabs_` + `TodayDate` (variable) + `.json`
  - Tip: use the `Text` action to combine: `tabs_[TodayDate].json`
- ✅ Check: **Overwrite if file exists** = ON

### 3. Name the shortcut: **"Weekly Tab Export"**

### 4. Set up weekly automation
- Go to **Automation** tab → **+** → **Time of Day**
- Time: Sunday, 7:55 AM (a few minutes before your Mac digest runs)
- Run: **Weekly Tab Export**
- ✅ Turn off "Ask Before Running"

---

## Output File Format

The Shortcut saves a file like:

```
iCloud Drive / WeeklyDigest / tabs_2026-03-16.json
```

Contents:
```json
[
  {"title": "Compound Engineering — Every", "url": "https://every.to/chain-of-thought/..."},
  {"title": "SVPG: Product Coaching and AI", "url": "https://www.svpg.com/product-coaching-and-ai/"},
  ...
]
```

---

## Manual Fallback (if "Find Tabs" isn't available)

If you're on iOS < 18.4, use Safari's built-in **Copy All Links**:

1. Long-press the tabs icon (bottom right in Safari)
2. Tap **"[N] Tabs"** → **"Copy Links"**
3. Paste into a text file saved to `iCloud Drive / WeeklyDigest / tabs_YYYY-MM-DD.txt`

The Mac script supports `.txt` files too — one URL per line is fine.

---

## Testing

After saving the Shortcut, tap **Run** once manually.
Then check iCloud Drive on your Mac:

```
~/Library/Mobile Documents/com~apple~CloudDocs/WeeklyDigest/
```

You should see a file like `tabs_2026-03-16.json`. If it's there, run:

```bash
python sources/tabs.py
```

and confirm the tabs are loaded correctly.
