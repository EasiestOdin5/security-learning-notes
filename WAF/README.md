# WAF Engineering Lab — Summary and Progress

Updated: 2026-10-24  
Status: **Lab 1 complete; Lab 2 (bot detection) next**

## Goal

Learn the internals of web application firewall (WAF) detection and enforcement for web security engineering roles. Favor a fully local, transparent ruleset over managed/black-box Cloudflare detection. Concentrate on rule logic rather than SIEM ingestion or LLM investigation.

## Local lab architecture

```text
Windows curl / browser / Burp
  -> localhost:8080 (Docker published on 127.0.0.1)
  -> "waf" container: Nginx + ModSecurity v3 + OWASP CRS v4
  -> Docker network "waf-lab"
  -> "backend" container: plain nginx:alpine on port 80
```

- Image: `owasp/modsecurity-crs:nginx` for WAF; `nginx:alpine` for backend.
- The backend is **not published** directly to Windows.
- Nginx reverse proxies HTTP from WAF to backend; Docker port publishing is a separate operation.
- Initial lab uses HTTP, not HTTPS, to focus on inspection. TLS termination can be added later.
- The Docker image exposes common settings via environment variables; use bind mounts for durable custom SecLang rules.
- Test only against this locally owned lab.

## Lab 1 — completed checkpoints

- [x] Verify Docker Desktop Linux engine and Docker Compose.
- [x] Pull OWASP ModSecurity CRS Nginx image.
- [x] Create bridge network `waf-lab`, run plain Nginx backend, run WAF reverse proxy.
- [x] Verify `curl -i http://localhost:8080/` returns 200 via WAF and backend.
- [x] Test SQLi request in `DetectionOnly`: HTTP 200 with detection logged.
- [x] Inspect actual CRS SQLi rule **942100** (`@detectSQLi` / libinjection).
- [x] Distinguish ModSecurity transformations (`utf8toUnicode`, `urlDecodeUni`, `removeNulls`) from libinjection token-based fingerprint classification; fingerprints are not necessarily cryptographic hashes.
- [x] Enable `MODSEC_RULE_ENGINE=On`: SQLi returned HTTP 403.
- [x] Inspect CRS blocking evaluator **949110**: accumulated per-request score compared using `@ge`; `deny` on threshold.
- [x] Raise `ANOMALY_INBOUND` from **5 to 10**: SQLi detected by 942100 but HTTP 200 because detection alone scored 5.
- [x] Combine SQLi and traversal/file-access input: multiple rules matched, total inbound anomaly score **45**, HTTP 403. Nine severity-2 (CRITICAL) detections at default 5 points each plus threshold evaluation (which does not contribute score).
- [x] Demonstrate a potential false positive in a **legitimate SQL-example search field**: `search` value `' OR '1'='1` triggered 942100.
- [x] Add a narrow runtime exclusion in REQUEST-900 for `ARGS:search` and rule 942100 at root path. Confirm no 942100 match for `search`, while `id` still triggered 942100.
- [x] Set `BLOCKING_PARANOIA=2`. Request `/?test=%2Fetc%2Fpasswd` triggered PL1 rules **930120**, **932160** and additional PL2 regex-based rule **932236**, scoring **15** against threshold 10 => 403.
- [x] Inspect rule 932236: `@rx` large Unix-command regex, in contrast with libinjection-based SQLi detection. Confirm `tag:'paranoia-level/2'`.

## Key rule IDs and behavior

| Rule | Role |
| --- | --- |
| 942100 | SQL injection detection through libinjection, severity CRITICAL |
| 930100 / 930110 | Path traversal-related detections seen in combined test |
| 930120 | OS file access attempt |
| 932160 | Unix shell/code pattern |
| 932236 | PL2 Unix command-injection regex detection |
| 949110 | Blocking evaluation on accumulated inbound anomaly score; not a detection-score contributor |

**Important:** CRS anomaly scores accumulate **within a single HTTP request**, not across all requests from an IP. Multiple rule hits may reflect overlapping signatures, not independent attacks. A 200 response does not mean no detection occurred.

## Local exclusion rule

Host file: `REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf`

```apache
SecRule REQUEST_FILENAME "@streq /" \
    "id:100001,phase:1,pass,nolog,ctl:ruleRemoveTargetById=942100;ARGS:search"
```

The exclusion removes only `ARGS:search` from rule `942100`, on root path. Other detection rules remain applicable; do not treat it as wholesale WAF bypass. `REQUEST_FILENAME` was chosen instead of `REQUEST_URI` because the latter includes the query string.

## Recreate the latest working configuration

From **Windows CMD** in the directory containing the exclusion file, assuming `backend` and `waf-lab` network still exist:

```cmd
docker stop waf
docker rm waf
docker run -d --name waf --network waf-lab -p 127.0.0.1:8080:8080 -e BACKEND=http://backend:80 -e MODSEC_RULE_ENGINE=On -e ANOMALY_INBOUND=10 -e BLOCKING_PARANOIA=2 -v "%cd%\REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf:/etc/modsecurity.d/owasp-crs/rules/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf:ro" owasp/modsecurity-crs:nginx
```

Inspect:

```cmd
docker ps
docker exec waf sh -c "grep 'setvar:tx.blocking_paranoia_level=' /etc/modsecurity.d/owasp-crs/crs-setup.conf"
docker logs waf --tail 5
```

Note: Interactively typed Windows CMD and batch files handle percent escaping differently. Be careful to distinguish literal `%%27` from URL-encoded `%27`.

## Learning conclusions

1. ModSecurity runs detection/enforcement; OWASP CRS supplies SecLang rules; Nginx handles proxying.
2. `942100` delegates detection to libinjection. Other CRS rules use pattern/regex operators such as `@rx` and `@pmFromFile`.
3. Rules accumulate severity-derived anomaly points; `949110` decides whether to interrupt based on the threshold.
4. Detection, logging, and enforcement are separate. `DetectionOnly` always permits requests; `On` can still permit detected requests that stay below a blocking threshold.
5. PL2 adds more detections, potentially improving coverage but raising false-positive risk.
6. Narrow target-specific exclusions are preferable to disabling entire detection categories.
7. Production WAF audit events are commonly analyzed through SIEMs, but this lab intentionally prioritizes rule mechanics over OpenSearch integration.

## Next work (not yet started)

### Lab 2 — Bot detection and mitigation
- [ ] Examine stateful request-rate detection and limitations of per-request CRS scoring.
- [ ] Generate **small, controlled, local** HTTP request sequences for baseline vs automated behavior.
- [ ] Compare rate-by-IP, endpoint targeting, sessions, and distributed patterns.
- [ ] Explain JA3/JA4 as TLS fingerprints and what instrumentation is needed to obtain them; current HTTP-only ModSecurity setup does **not** natively supply JA4.
- [ ] Implement rate limiting and test false positives for legitimate automation.

### Lab 3 — DDoS concepts and response
- [ ] Distinguish L3/L4 vs L7 attacks and what a reverse-proxy WAF can and cannot mitigate.
- [ ] Study sample telemetry and bounded local load tests; **do not create real traffic floods**.
- [ ] Compare mitigation decisions, impact, rollback, and availability.

### Optional later
- [ ] HTTPS/TLS termination and origin protection.
- [ ] Persistent local rule management / Docker Compose.
- [ ] Python/OpenSearch telemetry correlation only if it adds new learning value.

## Preferred lab method

Keep responses short, one concrete step at a time, explain why a command is being used, inspect actual output before continuing, and focus on understanding detection internals rather than simply completing setup steps.
