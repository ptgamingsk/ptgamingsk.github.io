#!/usr/bin/env python3
"""Refresh public Kick follower count for PTGamingSK (unofficial website endpoint)."""
import json
import pathlib
import subprocess
import time
from datetime import datetime, timezone

url = f"https://kick.com/api/v2/channels/ptgamingsk?_={time.time_ns()}"
result = subprocess.run(
    ["curl", "--fail", "--silent", "--show-error", "--location",
     "--max-time", "25", "--retry", "2", "--header", "Accept: application/json",
     "--header", "Cache-Control: no-cache, no-store, max-age=0",
     "--header", "Pragma: no-cache", "--user-agent", "Mozilla/5.0", url],
    capture_output=True, text=True, timeout=90, check=True,
)
payload = json.loads(result.stdout)
if str(payload.get("slug", "")).lower() != "ptgamingsk":
    raise SystemExit("Unexpected Kick channel; keeping previous statistics.")
followers = payload.get("followers_count")
if isinstance(followers, bool) or not str(followers).isdigit():
    raise SystemExit("Kick follower count unavailable; keeping previous statistics.")
target = pathlib.Path("assets/kick-stats.json")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    "followers": int(followers),
    "updatedAt": datetime.now(timezone.utc).isoformat(),
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Kick follower count refreshed: {followers}")
