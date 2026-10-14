# IAM Privilege Escalation Lab 01 — CreatePolicyVersion

**Date:** 2026-10-14  
**Status:** Completed (manual reproduction, CloudTrail analysis, basic local detector and tests)  
**Reference:** [AWS IAM privilege-escalation case-by-case walkthrough](2026-10-14-iam-privilege-escalation-reference.md), case 1

## Objective

Reproduce IAM policy-version privilege escalation, verify the sequence in CloudTrail, and build a first-pass Python detection with clear reporting and tests. The goal was a complete basic rule, **not** automated policy-diff analysis or historical AccessDenied correlation.

## Controlled lab

- IAM principal: `lab-attacker`; CLI profile: `lab-attacker`.
- Customer-managed policy: `lab-attacker-policy`, attached to the IAM user.
- Initial default policy (v1) allowed `iam:CreatePolicyVersion`, but not `iam:ListUsers`.
- The user performed `iam:ListUsers` and observed `AccessDenied`.
- Using the same IAM user's credentials, the user called `CreatePolicyVersion` with `setAsDefault=true`, activating v2. The new policy retained `iam:CreatePolicyVersion` and added `iam:ListUsers`.
- A subsequent `ListUsers` invocation succeeded. This demonstrates a narrowly scoped permission increase; `Action: "*"` was not needed.

**Outcome:** Privilege escalation demonstrated in the controlled environment.

## CloudTrail evidence

The three relevant operations were identified and correlated:

| Sequence | API | Observed result |
|---|---|---|
| 1 | `ListUsers` | `AccessDenied` |
| 2 | `CreatePolicyVersion` | Success, `setAsDefault=true` |
| 3 | `ListUsers` | Success |

- The same `userIdentity.arn` and `userIdentity.accessKeyId` were verified across all three events.
- The `CreatePolicyVersion` event was observed at **2026-10-14 18:16:03 UTC** (the log uses UTC).
- The event's `requestParameters.policyArn` pointed to `lab-attacker-policy`.
- The successful event had no `errorCode`, represented as `NaN` after pandas normalization.
- The newly downloaded CloudTrail JSON file used for detection contained **525 records**.

**Interpretation:** The timeline, matching principal and access key, activated policy, and before/after authorization results support the controlled lab conclusion. Matching a credential does not by itself prove authorization causality; the policy comparison and executed API results establish the scenario.

## Python tool workflow

```text
CloudTrail JSON filename (CLI argument)
    -> load_events()
    -> validate_cloudtrail()
    -> pd.json_normalize(Records)
    -> detect_create_policy_version(df)
    -> report_detections(alerts)
```

Detection predicate (first iteration):

```python
def detect_create_policy_version(df):
    events = find_events(df, event_name="CreatePolicyVersion")
    alerts = events[
        (events["requestParameters.setAsDefault"] == True)
        & (events["errorCode"].isna())
    ]
    return alerts
```

The detector returns **matching events** rather than printing or returning a Boolean. The separate `report_detections()` function prints the rule name, severity, time, actor, policy ARN, detection reason, and total alerts.

- Rule identifier: `IAM_DEFAULT_POLICY_VERSION_CREATED` (currently hardcoded in reporting).
- Initial severity: **MEDIUM**.
- Alert meaning: **investigation required**, not confirmed malicious privilege escalation.
- Example usage: `python cloudtrail_parser.py <cloudtrail-file.json>`.

The current GitHub `tool-engineering/cloudtrail_parser.py` is an **older checkpoint**. The latest detector and reporting code were developed and tested locally and **have not been uploaded or claimed as synchronized here**.

## Test results

Tests were run by the user using separate JSON inputs passed through the command-line loader.

| Case | Input condition | Expected | Observed |
|---|---|---|---|
| Positive | `CreatePolicyVersion`, `setAsDefault=true`, no API error | Alert | Alert — PASS |
| Negative | `CreatePolicyVersion`, `setAsDefault=false`, no API error | No alert | No alert — PASS |
| Negative | `CreatePolicyVersion`, `setAsDefault=true`, `errorCode=AccessDenied` | No alert | No alert — PASS |

The error-code negative case used an altered/simulated event, **not evidence of an actual AWS AccessDenied response** for the original policy-version creation.

## Known limitations and intentional deferrals

- Legitimate administrators may activate policy versions: **false positives** are possible.
- The rule does not inspect or compare policy documents, quantify newly added privileges, or prove escalation.
- It does not correlate prior denied calls and later successful operations automatically; correlation was done manually for this lab.
- It does not detect alternative policy activation operations (including the **separate next lab**, `SetDefaultPolicyVersion`) or `CreatePolicyVersion` calls with `setAsDefault=false`. This is the scope of the chosen first rule.
- `errorCode` and `requestParameters.setAsDefault` are assumed present as DataFrame columns for the tested input. More general missing-field handling is deferred.
- The rule name is hardcoded in the report, pending a later multi-rule design.
- No production alerting integration, alert suppression/tuning, broad policy impact analysis, or replay/unit-test harness was implemented.

## Completion and next step

**Lab 01 complete.** The exercise covered an end-to-end privilege escalation, manual CloudTrail investigation, first-pass detector, human-readable report, and positive/negative validation. Stop expanding this scenario for now.

**Next distinct lab:** `SetDefaultPolicyVersion` from the reference. Reuse the JSON loader, detector/report separation, and test approach. Do not store unredacted event histories, credentials, IP addresses, or access-key identifiers in the public repository.
