"""
Render the ranked digest as a clean HTML email and plain-text fallback.
"""

from datetime import datetime

CATEGORY_COLORS = {
    "technology":   "#3B82F6",  # blue
    "productivity": "#8B5CF6",  # purple
    "culture":      "#EC4899",  # pink
    "finance":      "#10B981",  # green
    "health":       "#F59E0B",  # amber
    "personal":     "#6B7280",  # gray
    "news":         "#EF4444",  # red
    "shopping":     "#F97316",  # orange
    "other":        "#9CA3AF",  # light gray
}

SOURCE_LABELS = {
    "tab":   "🔖 Tab",
    "email": "✉️ Email",
}


def _score_bar(score: int) -> str:
    filled = round(score / 2)  # 0–5 blocks
    empty = 5 - filled
    return "█" * filled + "░" * empty


def _category_pill(category: str) -> str:
    color = CATEGORY_COLORS.get(category.lower(), CATEGORY_COLORS["other"])
    label = category.capitalize()
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:12px;font-size:11px;font-weight:600;'
        f'letter-spacing:0.5px;">{label}</span>'
    )


def _score_badge(score: int) -> str:
    if score >= 8:
        bg, text = "#10B981", "#fff"
    elif score >= 5:
        bg, text = "#F59E0B", "#fff"
    else:
        bg, text = "#E5E7EB", "#6B7280"
    return (
        f'<span style="background:{bg};color:{text};padding:3px 9px;'
        f'border-radius:20px;font-size:13px;font-weight:700;">'
        f'{score}/10</span>'
    )


def render_html(ranked_items: list[dict], week_label: str = None) -> str:
    if week_label is None:
        week_label = datetime.now().strftime("Week of %B %-d, %Y")

    total = len(ranked_items)
    tabs = sum(1 for i in ranked_items if i.get("source") == "tab")
    emails = total - tabs

    # Build item rows
    item_rows = []
    for item in ranked_items:
        rank = item.get("rank", "")
        title = item.get("title") or "(no title)"
        url = item.get("url", "#")
        summary = item.get("summary", "")
        score = int(item.get("score", 5))
        category = item.get("category", "other")
        source = item.get("source", "tab")
        source_label = SOURCE_LABELS.get(source, source)

        row = f"""
        <tr>
          <td style="padding:16px 20px;border-bottom:1px solid #F3F4F6;vertical-align:top;">
            <div style="display:flex;align-items:flex-start;gap:12px;">
              <div style="min-width:28px;text-align:center;color:#9CA3AF;font-size:13px;
                          font-weight:700;padding-top:2px;">#{rank}</div>
              <div style="flex:1;">
                <div style="margin-bottom:6px;">
                  {_score_badge(score)}&nbsp;&nbsp;
                  {_category_pill(category)}&nbsp;&nbsp;
                  <span style="color:#9CA3AF;font-size:12px;">{source_label}</span>
                </div>
                <div style="margin-bottom:4px;">
                  <a href="{url}" style="color:#1D4ED8;font-weight:600;font-size:15px;
                                         text-decoration:none;">{title}</a>
                </div>
                <div style="color:#374151;font-size:14px;line-height:1.5;">{summary}</div>
                <div style="margin-top:4px;">
                  <a href="{url}" style="color:#9CA3AF;font-size:11px;
                                         text-decoration:none;word-break:break-all;">{url[:80]}{'…' if len(url) > 80 else ''}</a>
                </div>
              </div>
            </div>
          </td>
        </tr>"""
        item_rows.append(row)

    items_html = "\n".join(item_rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Weekly Digest — {week_label}</title>
</head>
<body style="margin:0;padding:0;background:#F9FAFB;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F9FAFB;padding:32px 16px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;
                    box-shadow:0 1px 3px rgba(0,0,0,0.1);max-width:640px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1E40AF,#7C3AED);
                      padding:28px 32px;text-align:center;">
            <div style="color:#fff;font-size:24px;font-weight:700;
                        letter-spacing:-0.5px;">Weekly Digest</div>
            <div style="color:rgba(255,255,255,0.8);font-size:14px;
                        margin-top:4px;">{week_label}</div>
          </td>
        </tr>

        <!-- Stats bar -->
        <tr>
          <td style="background:#F8FAFF;padding:14px 32px;border-bottom:1px solid #E5E7EB;">
            <div style="display:flex;gap:24px;font-size:13px;color:#6B7280;
                        justify-content:center;text-align:center;">
              <span><strong style="color:#111827;">{total}</strong> total items</span>
              <span>·</span>
              <span><strong style="color:#111827;">{tabs}</strong> tabs</span>
              <span>·</span>
              <span><strong style="color:#111827;">{emails}</strong> emails</span>
            </div>
          </td>
        </tr>

        <!-- Items -->
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0">
{items_html}
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px;background:#F9FAFB;border-top:1px solid #E5E7EB;
                      text-align:center;">
            <div style="color:#9CA3AF;font-size:12px;">
              Generated by Weekly Digest · {datetime.now().strftime("%B %-d, %Y at %-I:%M %p")}
            </div>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def render_text(ranked_items: list[dict], week_label: str = None) -> str:
    if week_label is None:
        week_label = datetime.now().strftime("Week of %B %-d, %Y")

    lines = [
        f"WEEKLY DIGEST — {week_label}",
        "=" * 60,
        "",
    ]

    for item in ranked_items:
        rank = item.get("rank", "")
        title = item.get("title") or "(no title)"
        url = item.get("url", "")
        summary = item.get("summary", "")
        score = item.get("score", "")
        category = item.get("category", "")
        source = item.get("source", "tab")

        lines.append(f"#{rank} [{score}/10] [{category}] [{source}]")
        lines.append(title)
        lines.append(url)
        if summary:
            lines.append(summary)
        lines.append("")

    lines.append("-" * 60)
    lines.append(f"Generated {datetime.now().strftime('%B %-d, %Y at %-I:%M %p')}")
    return "\n".join(lines)


if __name__ == "__main__":
    mock = [
        {
            "rank": 1, "title": "Compound Engineering", "url": "https://every.to/example",
            "source": "tab", "summary": "A detailed look at how to build software with AI agents.",
            "score": 9, "category": "technology",
        },
        {
            "rank": 2, "title": "Your weekly newsletter", "url": "https://example.com/news",
            "source": "email", "summary": "This week in productivity and tools.",
            "score": 7, "category": "productivity",
        },
    ]
    html = render_html(mock)
    with open("/tmp/digest_preview.html", "w") as f:
        f.write(html)
    print("Preview written to /tmp/digest_preview.html")
    print(render_text(mock))
