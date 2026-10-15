# Tool Engineering Progress

**Baseline date:** 2026-10-11  
**Last updated:** 2026-10-14  
**Scope:** Python implementation and security-tool engineering, tracked separately from the root security-skills matrix.

## Baseline / Current / Goal

The initial and current scores remain unchanged pending an independent, end-to-end implementation review. These are **provisional coaching estimates (0–10)** from guided exercises, not standardized scores or industry percentiles. Goals are proposed working targets for developing a reasonably independent internal security-tool builder; they are not claimed achievements.

| Skill | Initial | Current | Proposed goal | Change | Evidence confidence |
|---|---:|---:|---:|---:|---|
| Python fundamentals | 6.0 | 6.0 | 8.0 | 0 | High |
| Data structures | 6.5 | 6.5 | 8.0 | 0 | High |
| Functions and modularity | 6.0 | 6.0 | 8.0 | 0 | Moderate |
| Error handling | 6.0 | 6.0 | 8.0 | 0 | High |
| Testing fundamentals | 5.5 | 5.5 | 8.0 | 0 | Moderate |
| Debugging | 5.0 | 5.0 | 8.0 | 0 | Low |
| Algorithm / data design | 7.0 | 7.0 | 8.0 | 0 | Moderate |
| Software architecture | 6.5 | 6.5 | 8.0 | 0 | Low |
| Independent implementation | 5.0 | 5.0 | 8.0 | 0 | Moderate |

**Interpretation:** Design and investigation reasoning appears stronger than implementation fluency. The current baseline reflects guided code-writing and corrections—not independent end-to-end delivery. Low-confidence assessments, particularly debugging and architecture, need practical evidence before a firm conclusion. Do not average these scores into a professional rank.

## Evidence — Initial checkpoint, 2026-10-11

See [detailed checkpoint](2026-10-11-python-cloudtrail-checkpoint.md).

**Demonstrated in conversation:** nested dictionaries/lists; full-scan versus indexed lookup reasoning; JSON loading; expected exceptions; separate loader and validator functions; CloudTrail `Records` shape and event-type checks; tuple return values; positive and negative assertions; basic data-driven test runner with correctly updated index and Boolean comparison.

**Correction history:** initial confusion about shallow references, inconsistent dictionary keys, accidentally using `exit` instead of `exit()`, comparing validation tuple to Boolean, reinitializing test index in loop, variable-name typo. Corrections were incorporated after review.

**Not yet established:** independent build of a complete investigation utility, actual automated test results on the local 20,000+ event dataset, debugging without hints, sustained maintainability, and scalable file processing.

## Project milestones

| Milestone | Status | Completion evidence required |
|---|---|---|
| Read JSON and handle missing/invalid file | Code written; reviewed | Run against valid and invalid local fixtures |
| Validate top-level structure and Records entries | Code written; reviewed | Repeatable tests cover all expected cases |
| Data-driven validation tests | Basic function written; reviewed | Run test cases and record pass/fail |
| Index events by IAM username | Not started as integrated code | Independent implementation and verified grouping |
| Search/report investigation findings | Two rules locally implemented and user-tested; first version committed | Reproduce full rule+report workflow with committed code and sanitized fixtures |
| End-to-end CLI and safe error reporting | CLI file input and detection report locally tested; negative error paths not fully verified | Exit codes, malformed input behavior, repeatable runs |
| Handle assumed roles, duplicates, large files | Future | Explicit requirements and measured verification |

## Scoring rules

- Preserve the **Initial** column permanently as the baseline.
- Update **Current** only for dated, demonstrated evidence of new capability—not for agreement, recognition, or successful answers to guided conceptual questions alone.
- Log the date, task, level of assistance, test evidence, and reason for any score change.
- Distinguish **implemented**, **locally tested**, and **independently reproduced**.
- Keep goals stable unless deliberately revisited; adjust assessments when contrary evidence warrants it.
- Do not commit CloudTrail data, account identifiers, IP addresses, or credentials.

## Evidence — October 14, 2026: CreatePolicyVersion privilege-escalation lab

**Lab write-up:** [2026-10-14-create-policy-version-lab.md](2026-10-14-create-policy-version-lab.md).

**Hands-on security evidence:** Reproduced escalation with a customer-managed IAM policy: `ListUsers` was denied, `CreatePolicyVersion` activated a version granting `iam:ListUsers`, and `ListUsers` then succeeded. Manually verified the same IAM principal and access key across denied, change, and successful events.

**Tool-engineering evidence (user-tested locally):** Ingested a fresh 525-event CloudTrail JSON export via CLI filename argument, normalized events using pandas, filtered successful `CreatePolicyVersion` activity with `setAsDefault=True`, and produced a human-readable detection report. Three end-to-end JSON test inputs produced expected results: positive alert; no alert when `setAsDefault=False`; no alert when an `AccessDenied` error was present. The final denied event was a simulated modification of a CloudTrail record.

**Scope/assistance:** Guided implementation and manual tests; no automated test suite or independent code audit yet. No raw CloudTrail records committed.

**Score changes:** None. This lab is concrete progress, but scores remain unchanged until the current local implementation is reviewed and reproducibly tested. Preserve the initial/current/goal matrix.

**Source artifacts:** [2026-10-11-cloudtrail_parser.py](2026-10-11-cloudtrail_parser.py) preserves the initial loader/validator checkpoint. [2026-10-14-cloudtrail_parser.py](2026-10-14-cloudtrail_parser.py) is the user-provided and committed **Lab 1** detector/report. It does not yet contain the two-rule Lab 2 refactor.

## Evidence — October 14, 2026: SetDefaultPolicyVersion privilege-escalation lab

**Lab write-up:** [2026-10-14-set-default-policy-version-lab.md](2026-10-14-set-default-policy-version-lab.md).

**Hands-on security evidence:** Created a v3 default of the attached customer-managed lab policy that allowed `iam:SetDefaultPolicyVersion`; v2 remained inactive with `iam:ListUsers`. Switched default from v3 to v2 using attacker credentials, then successfully invoked `ListUsers`. Located the CloudTrail `SetDefaultPolicyVersion` event and its requested v2 target. The event does not record the previous default version.

**Tool-engineering evidence (locally tested):** Added a successful-API-call `SetDefaultPolicyVersion` rule, unified detector results into a dictionary containing `rule`, `severity`, `reason`, and `alerts`, generalized the reporter to consume this interface, and adopted a list of detector functions as a simple registry. Latest CloudTrail JSON generated the expected detections; an older JSON predating the operation generated no matching Lab 2 detections. Failed-API negative testing remains unverified.

**Assessment:** Faster scenario design and implementation than Lab 1, with reusable architecture rather than repetitive code. User independently raised key design concerns; implementation remained guided. This evidence supports a qualitative improvement in modularity and tool-design reasoning, but doesn't alone justify a defensible numerical score change.

**Score changes:** None. Preserve original baselines and current score until combined code and reproducible tests are reviewed.

**Source status:** The latest two-detector Python script is **local only** as of this entry. The committed [October 14 parser](2026-10-14-cloudtrail_parser.py) is the earlier Lab 1 version. Do not mislabel it as Lab 2 code.

## Next session

Receive and review the current two-detector script, then commit it as a new dated/versioned checkpoint without losing the Lab 1 version. Continue to the next privilege-escalation case; defer advanced false-positive tuning and historical policy-diff analysis. Keep real AWS event data out of the public repo.
