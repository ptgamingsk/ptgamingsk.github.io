#!/usr/bin/env python3
"""Maintain public APK release notes from the message of the APK upload commit.

Only explicitly described changes are recorded. The APK binary does not tell us
which bugs were fixed; generic upload commit messages never become release notes.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def upload_message():
    if os.environ.get("GITHUB_EVENT_NAME") != "push":
        return None
    event_file = os.environ.get("GITHUB_EVENT_PATH")
    if not event_file:
        return None
    event = json.loads(Path(event_file).read_text(encoding="utf-8"))
    # A push can contain multiple commits. Use the most recent commit that
    # actually changed the Android APK, not an unrelated workflow edit.
    for commit in reversed(event.get("commits", [])):
        changed = set(commit.get("added", [])) | set(commit.get("modified", []))
        if "app-release.apk" in changed:
            return str(commit.get("message", ""))
    return None


def release_notes(message):
    if not message:
        return []
    rows = [row.strip() for row in message.splitlines() if row.strip()]
    if not rows:
        return []
    subject = rows[0]
    prefix = re.match(r"^(?:fix|feat|app|release|changelog|zmeny|oprava|novinka)\s*:\s*(.+)$", subject, re.I)
    if prefix:
        subject = prefix.group(1).strip()
    elif not re.search(r"\b(oprav|pridan|pridat|vyleps|vylepš|zmenen|zmenil|fix|added|improv|bug|new feature)\w*", subject, re.I):
        subject = ""
    notes = [subject] if subject else []
    # Optional bullet points from the GitHub commit description.
    for row in rows[1:]:
        if row.startswith(("- ", "* ")):
            notes.append(row[2:].strip())
    generic = re.compile(r"^(?:update|upload|add|replace|nahrat|nahrať|aktualizacia|aktualizácia|vydanie)\s*(?:(?:app[-_ ]?release\.?apk)|(?:apk)|(?:v?\d+(?:\.\d+)+))?\s*$", re.I)
    clean = []
    for note in notes:
        note = " ".join(note.split())[:240]
        if 8 <= len(note) <= 240 and not generic.fullmatch(note) and note not in clean:
            clean.append(note)
    return clean[:8]


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: update_app_changelog.py <versionCode> <versionName>")
    version_code = int(sys.argv[1])
    version_name = sys.argv[2].strip()
    if version_code < 1 or not re.fullmatch(r"\d+(?:\.\d+){1,2}", version_name):
        raise SystemExit("Invalid Android version; release notes unchanged.")

    message = upload_message()
    if message is None:
        print("No new APK upload in this event; release notes unchanged.")
        return

    path = Path("app-changelog.json")
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"releases": []}
    releases = data.get("releases", [])
    if not isinstance(releases, list):
        raise SystemExit("Invalid app-changelog.json format.")
    notes = release_notes(message)
    entry = next((item for item in releases if isinstance(item, dict) and item.get("versionCode") == version_code), None)
    if entry is None:
        releases.append({
            "versionName": version_name,
            "versionCode": version_code,
            "publishedAt": datetime.now(timezone.utc).date().isoformat(),
            "changes": notes
        })
    elif notes:
        existing = entry.get("changes", [])
        if not isinstance(existing, list):
            existing = []
        for note in notes:
            if note not in existing:
                existing.append(note)
        entry["changes"] = existing[:12]
    data["releases"] = sorted(releases, key=lambda item: int(item.get("versionCode", 0)), reverse=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if notes:
        print(f"Recorded {len(notes)} changelog note(s) for Android V{version_name}.")
    else:
        print(f"Recorded Android V{version_name} without unverified change claims.")


if __name__ == "__main__":
    main()
