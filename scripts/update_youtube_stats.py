#!/usr/bin/env python3
"""Fetch public YouTube channel statistics. Requires YOUTUBE_API_KEY environment secret."""
import json
import os
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone

key = os.environ.get("YOUTUBE_API_KEY", "").strip()
if not key:
    raise SystemExit("YOUTUBE_API_KEY is not configured; no stats published.")
query = urllib.parse.urlencode({"part": "statistics,snippet", "forHandle": "@PTGamingSK", "key": key})
request = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?" + query, headers={"User-Agent": "PTGamingSK-Website-Stats/1.0"})
with urllib.request.urlopen(request, timeout=25) as response:
    payload = json.load(response)
items = payload.get("items") or []
if len(items) != 1 or items[0].get("snippet", {}).get("title", "").lower() != "ptgamingsk":
    raise SystemExit("YouTube channel could not be verified; no stats published.")
statistics = items[0].get("statistics", {})
if statistics.get("hiddenSubscriberCount", False) or "subscriberCount" not in statistics:
    raise SystemExit("Subscriber count is unavailable; no stats published.")
result = {"subscribers": int(statistics["subscriberCount"]), "views": int(statistics.get("viewCount", 0)), "videos": int(statistics.get("videoCount", 0)), "updatedAt": datetime.now(timezone.utc).isoformat()}
target = pathlib.Path("assets/youtube-stats.json")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("YouTube statistics refreshed.")
