# Checkpoint: Browser execution, HTTP responses and CORS
Date: 2026-10-09, 01:00 America/Los_Angeles
Scope: Gap coaching only, separate from other labs and their scores.

## Starting gaps
Could recognize attacks but browser/server architecture was unsettled. Initially conflated cookie scope with origin, Secure with HTTPS upgrading, CORS with port mapping or JavaScript execution permission, and which server grants cross-origin access.

## Demonstrated evidence
All implementation below was guided, not independent mastery.
- Created/activated a Windows Python virtual environment and installed FastAPI/Uvicorn.
- Served HTML at / and JSON at /analysis; predicted and observed the JSON response.
- Observed Content-Type: text/html; charset=utf-8.
- Verified original paragraph in Network > Response and changed paragraph in Elements: server supplied JavaScript, browser executed it and modified the DOM.
- Observed a separate /analysis background request made by fetch(), receiving {"result":"suspicious"}.
- Ran the same app on 127.0.0.1 ports 8000 and 8001.
- Predicted cross-origin JavaScript could not read data without CORS.
- Observed 200 OK without Access-Control-Allow-Origin.
- Configured CORSMiddleware to allow http://127.0.0.1:8000; after restarting 8001, observed the paragraph become suspicious and the matching response header.
- Changed allowed origin to 8002 and observed the permission header disappear.
- Explained why the responding API must grant access; transferred that reasoning to a hypothetical browser-to-Amazon request.
- Recognized that shared main.py configures both instances, although origin 8000 permission is relevant to the cross-origin response from 8001.

## Exact corrections
- Origin = scheme + hostname + port; paths do not change origin, subdomains do.
- CORS does not map ports or grant JavaScript execution permission.
- For this simple GET, HTTP succeeds while the browser denies JavaScript response access.
- The destination API grants permission, not the server that supplied the requesting page.
- FastAPI middleware omits Access-Control-Allow-Origin for a disallowed origin rather than returning the configured but mismatched origin.
- Python HTTP clients retrieve data without rendering HTML or executing embedded JavaScript; they do not enforce browser CORS.

## Current state and limitations
Local folder: web-gap-lab, main.py; two Uvicorn instances on 127.0.0.1:8000 and :8001.
Both were instructed to use --reload after stale code on 8001 delayed the observed CORS change.
HTML fetches http://127.0.0.1:8001/analysis. A successful configuration allows http://127.0.0.1:8000.
After testing allowed origin 8002, restoration to 8000 was instructed but not confirmed.
Servers were not reported stopped.
No independent reconstruction or retention check completed.
Python client was supplied but its execution/output was not confirmed.
Preflight, credentials, HttpOnly, SameSite, CSRF and cookie hands-on behavior remain untested.

## Next step
Run the direct Python client below and compare its output with browser behavior. Then test a cross-origin JSON POST and OPTIONS preflight, predicting before testing.

```python
from urllib.request import urlopen

with urlopen("http://127.0.0.1:8001/analysis") as response:
    print("HTTP status:", response.status)
    print("CORS header:", response.headers.get("Access-Control-Allow-Origin"))
    print("Body:", response.read().decode("utf-8"))
```

## Resume instruction
Continue one concept or practical step at a time. Brief theory before commands; user performs learning-critical steps. Keep gaps separate from existing cloud/AI/Kubernetes labs. Assess recall, explanation, investigation and independent implementation separately; mark untested skills unknown.
