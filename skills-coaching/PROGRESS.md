# Cybersecurity Practical Skills Coaching

Baseline: 2026-10-08 (America/Los_Angeles)
Last updated: 2026-10-09
Purpose: Measure whether architectural understanding and investigative reasoning transfer to independent practical work.

## Assessment rules

Track four dimensions separately: recall, explanation, investigation, and independent implementation.
Unknown means untested, not unable. A corrected answer demonstrates learning in the moment, not retention.
Guided completion is recorded separately from independent work. No percentile or numerical mastery claims.
Keep this baseline fixed; append dated evidence and update current status. Existing PROGRESS.md scores are historical context, not proof of mastery in these specific tasks.
At checkpoints, record demonstrated skills, unresolved gaps, completed exercises, and the next step.
No live home-network changes or paid resources without prior approval.

## Initial baseline and goals

| Area | Initial evidence | Unresolved or untested | Practical goal |
|---|---|---|---|
| Web and modern identity | Recognized cookie-held session IDs and session hijacking; explained HTTP interception versus TLS encryption | Initially conflated cookie scope with same origin and Secure with HTTPS upgrading. HttpOnly, SameSite, CORS, CSRF mechanics, OIDC/SAML flows and independent implementation untested | Explain request/credential/trust flows; predict browser behavior; verify with developer tools; build and investigate a small session-based app |
| Cloud architecture and investigation | Prior guided Identity Center, permission-set, IAM-role, VPC, CloudTrail and boto3 work is recorded in the repository | Fresh independent architecture reconstruction, policy troubleshooting and incident reconstruction untested in this coaching series | Map principals, sessions, permissions, network paths and telemetry; investigate an unfamiliar failure or incident with evidence |
| Network architecture and visibility | Explained TLS transport encryption; reports prior TCP/DNS/PCAP study and device discovery | Sensor placement, device attribution, session triage, DNS/PKI trust, packet filtering and stream extraction untested | Design a visibility plan; identify devices; narrow a capture; reconstruct sessions; distinguish encrypted metadata from recoverable content |
| Python and evidence processing | Reports existing small FastAPI/AI labs, structured outputs, tool restrictions and approval gates | Independent parsing, normalization, error handling, testing and repeatable deployment untested here | Build a small evidence processor independently; preserve source evidence; produce reproducible output |
| Incident response and forensic workflow | Explained stolen-session replay and considered multiple observation points | Independent hypothesis ranking, email-header analysis, timelines and cross-source correlation untested here | Separate observations from hypotheses; collect evidence; test alternatives; state supported conclusions and limitations |

Background strengths (self-report unless tested here): malware analysis, EDR and Windows internals.
These five priorities remain provisional. Introduce Linux, containers, threat modeling or data-handling prerequisites only when a task requires them.

## Current demonstrated skills

| Skill | Evidence | Current status |
|---|---|---|
| Session identification | Said session ID is usually stored in a cookie | Basic explanation demonstrated |
| Session hijacking | Predicted replay may hijack a session depending on controls | Basic investigative reasoning demonstrated |
| Cookie Domain matching | Correctly predicted Domain=example.com includes api.example.com, then no Domain excludes that host | Scenario prediction demonstrated after instruction; retention untested |
| Secure attribute | Initially predicted HTTPS upgrading; subsequently stated only HTTPS sends the cookie | Corrected understanding; retention and practical verification untested |
| HTTP/TLS exposure | Explained HTTP cookie visibility and encrypted HTTPS communication | Explanation demonstrated |
| Cookie scope versus origin | Required explicit distinction between hostname/domain cookie matching and scheme/host/port origin | Independent transfer untested |
| JavaScript cookie access / HttpOnly | Diagnostic question pending | Unknown |
| Hands-on browser verification | No exercise completed in this series | Unknown |
| Independent session implementation | No exercise completed in this series | Unknown |

## Dated evidence

### 2026-10-08 — Session and cookie diagnosis

Completed: verbal diagnostic scenarios only; no browser capture, code exercise or deployment.
Corrections:
- Cookie stores an identifier in the server-side-session model; the server stores the associated session record.
- Missing Domain makes a cookie host-only; Domain=example.com includes that host and its subdomains.
- Cookie matching is different from same-origin policy; cookie scope does not use ports.
- Secure restricts sending to HTTPS in the example.com scenarios; it does not upgrade HTTP.
- HTTPS protects transport, not against malicious code already executing with access inside a page or endpoint.

Investigation discussion: similarly themed suspicious emails prompted hypotheses about common observation points. No email headers or messages were inspected, and no compromise or causal connection was established.
Only sanitized learning conclusions belong in public notes; do not include private email contents, identifiers, credentials or unrelated personal details.

## Next step

Verify the direct Python HTTP client, then test JSON POST preflight. See the current checkpoint below.

## 2026-10-09 checkpoint

[HTTP, DOM and CORS evidence](2026-10-09-http-dom-cors-checkpoint.md)

Guided practical evidence now supersedes the baseline's initially untested browser tasks:
- Verified original HTTP response versus JavaScript-modified DOM.
- Observed background JSON fetch and cross-origin GET returning 200 without readable JavaScript access.
- Configured and verified allowed-origin response headers; tested omission for a disallowed origin.
- Explained destination-controlled permission and transferred it to a new scenario.
Independent reconstruction, retention, direct Python execution, preflight and credential/cookie interactions remain untested.
This coaching is topic-driven and separate from other labs; no changes to their scores.

## Update format

Date:
Task and prediction:
Observed result:
Assistance required:
Evidence for recall / explanation / investigation / independent implementation:
Exact correction:
Unresolved gap:
Next step:
