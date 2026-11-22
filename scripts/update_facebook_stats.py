#!/usr/bin/env python3
"""Update public Facebook follower count using a private Meta Page access token."""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

page_id = os.environ.get("FACEBOOK_PAGE_ID", "").strip()
token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
if not page_id or not token:
    raise SystemExit("Missing FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN GitHub Actions secret")

query = urllib.parse.urlencode({"fields": "id,name,followers_count", "access_token": token})
url = "https://graph.facebook.com/v25.0/" + urllib.parse.quote(page_id, safe="") + "?" + query
try:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "PTGamingSK-Stats/1.0"}), timeout=25) as response:
        data = json.load(response)
except Exception:
    raise SystemExit("Meta API request failed. Check token, page ID and permissions; existing data remains unchanged.") from None
count = data.get("followers_count")
if isinstance(count, bool) or not isinstance(count, int) or count < 0:
    raise SystemExit("Meta API did not return a valid followers_count; existing data remains unchanged")
if str(data.get("id")) != page_id:
    raise SystemExit("Unexpected Facebook page ID; existing data remains unchanged")
output = {"followers": count, "updatedAt": datetime.now(timezone.utc).isoformat()}
path = Path("assets/facebook-stats.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Facebook follower statistics updated successfully")
