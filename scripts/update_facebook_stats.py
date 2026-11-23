#!/usr/bin/env python3
"""Update public Facebook follower count using a private Meta Page access token.

Only print sanitized API error metadata, never tokens or full request URLs.
"""
import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

page_id = "1502729262914235"
token = os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip()
if not token:
    raise SystemExit("FACEBOOK_PAGE_TOKEN GitHub secret is missing or empty. Existing stats unchanged.")

query = urllib.parse.urlencode({"fields": "id,name,followers_count", "access_token": token})
url = "https://graph.facebook.com/v25.0/" + urllib.parse.quote(page_id, safe="") + "?" + query
request = urllib.request.Request(url, headers={"User-Agent": "PTGamingSK-Stats/1.0"})

try:
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.load(response)
except urllib.error.HTTPError as exc:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
        api_error = payload.get("error", {})
        code = api_error.get("code", "unknown")
        subcode = api_error.get("error_subcode", "none")
        error_type = api_error.get("type", "unknown")
        if not isinstance(code, int):
            code = "unknown"
        if not isinstance(subcode, int):
            subcode = "none"
        if error_type not in ("OAuthException", "GraphMethodException", "FacebookApiException"):
            error_type = "other"
        raise SystemExit(
            f"Meta Graph API HTTP {exc.code}; type={error_type}; "
            f"code={code}; subcode={subcode}. "
            "Check Facebook Page token, permissions, and Page ID. Existing stats unchanged."
        )
    except (ValueError, UnicodeError, AttributeError):
        raise SystemExit(
            f"Meta Graph API returned HTTP {exc.code}. Existing stats unchanged."
        ) from None
except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
    raise SystemExit(
        f"Meta Graph API connection failed ({type(exc).__name__}). Existing stats unchanged."
    ) from None
except (ValueError, UnicodeError):
    raise SystemExit("Meta Graph API returned invalid JSON. Existing stats unchanged.") from None

if not isinstance(data, dict):
    raise SystemExit("Meta Graph API returned an unexpected response. Existing stats unchanged.")
count = data.get("followers_count")
if isinstance(count, bool) or not isinstance(count, int) or count < 0:
    raise SystemExit(
        "Meta Graph API did not return a valid followers_count. "
        "Check Page permissions and API access. Existing stats unchanged."
    )
if str(data.get("id")) != page_id:
    raise SystemExit("Unexpected Facebook Page ID. Existing stats unchanged.")

output = {"followers": count, "updatedAt": datetime.now(timezone.utc).isoformat()}
path = Path("assets/facebook-stats.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Facebook follower statistics updated successfully")
