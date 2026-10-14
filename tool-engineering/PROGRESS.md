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
| Search/report investigation findings | Locally implemented and tested for one rule | Reproduce full rule+report workflow with committed code and sanitized fixtures |
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

**Source artifact:** [2026-10-11-cloudtrail_parser.py](2026-10-11-cloudtrail_parser.py) is the *older October 11 checkpoint*, date-prefixed for clarity. It does **not** contain the locally tested October 14 detector/report. Await the latest local script before committing a date-prefixed October 14 source file.

## Next session

Upload and review the current locally tested parser/detector, commit it as `2026-10-14-cloudtrail_parser.py`, and verify it on sanitized test fixtures; then start the separate `SetDefaultPolicyVersion` technique. Keep older checkpoints and real AWS event data separate.
