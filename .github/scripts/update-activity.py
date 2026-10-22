#!/usr/bin/env python3
"""ดึงกิจกรรมล่าสุดจาก GitHub แล้วอัปเดตส่วน Recent Activity ใน README.md"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = "saharatyokthuan"
README_PATH = "README.md"
MARKER_START = "<!-- recent-activity:start -->"
MARKER_END = "<!-- recent-activity:end -->"
ANCHOR = "### 📫 Connect with me"

EVENT_LABELS = {
    "PushEvent": "push",
    "PullRequestEvent": "pull request",
    "IssuesEvent": "issue",
    "CreateEvent": "สร้าง",
    "WatchEvent": "star",
    "ForkEvent": "fork",
}


def fetch_events(token=None):
    """ดึง public events ของผู้ใช้จาก GitHub REST API"""
    url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=30"
    req = urllib.request.Request(url, headers={"User-Agent": "recent-activity-script"})
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def format_thai_time(iso_str):
    """แปลงเวลา ISO 8601 เป็นรูปแบบอ่านง่าย (เวลาไทย UTC+7)"""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_th = dt.astimezone(timezone(timedelta(hours=7)))
        return dt_th.strftime("%d %b %Y, %H:%M")
    except Exception:
        return iso_str


def format_event(ev):
    """แปลง event object เป็นข้อความ markdown บรรทัดเดียว"""
    etype = ev.get("type", "")
    repo = ev.get("repo", {}).get("name", "")
    created = ev.get("created_at", "")
    when = format_thai_time(created)
    label = EVENT_LABELS.get(etype, etype)
    payload = ev.get("payload", {})
    action = ""

    if etype == "PushEvent":
        size = payload.get("size", 0)
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/") else ref
        action = f"push {size} commit{'s' if size != 1 else ''} ไปยัง `{branch}`"
    elif etype == "PullRequestEvent":
        action = payload.get("action", "")
        num = payload.get("pull_request", {}).get("number", "")
        action = f"{action} PR #{num}"
    elif etype == "IssuesEvent":
        action = payload.get("action", "")
        num = payload.get("issue", {}).get("number", "")
        action = f"{action} issue #{num}"
    elif etype == "CreateEvent":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref", "")
        action = f"สร้าง {ref_type} `{ref}`"
    elif etype == "WatchEvent":
        action = "star repository"
    elif etype == "ForkEvent":
        action = "fork repository"

    return f"- [{when}] **{label}**: {action} ใน [{repo}](https://github.com/{repo})"


def update_readme(events):
    """แทรก/อัปเดตบล็อก Recent Activity ใน README.md"""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    block_lines = [MARKER_START]
    if events:
        for ev in events[:10]:
            block_lines.append(format_event(ev))
    else:
        block_lines.append("_ยังไม่มีกิจกรรมล่าสุด_")
    block_lines.append(MARKER_END)
    new_block = "\n".join(block_lines)

    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.DOTALL)
    replacement = new_block

    if pattern.search(content):
        content = pattern.sub(replacement, content)
    else:
        section = (
            "\n### 🔥 Recent Activity\n\n" + new_block + "\n"
        )
        content = content.replace(ANCHOR, section + ANCHOR, 1)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    try:
        events = fetch_events(token)
    except Exception as e:
        print(f"❌ ดึงข้อมูลกิจกรรมไม่สำเร็จ: {e}", file=sys.stderr)
        sys.exit(1)

    update_readme(events)
    print(f"✅ อัปเดต Recent Activity เรียบร้อย ({len(events)} รายการ)")


if __name__ == "__main__":
    main()
