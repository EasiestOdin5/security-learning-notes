# IAM Privilege Escalation Lab 02 — SetDefaultPolicyVersion

**Date:** 2026-10-14  
**Status:** Lab reproduced; CloudTrail inspected; basic detector locally tested; current code not yet synchronized to GitHub  
**Reference:** [IAM privilege-escalation reference, case 2](iam-privilege-escalation-reference.md)

## Goal

Reproduce privilege escalation by selecting an **existing nondefault** IAM policy version and extend the existing Python CloudTrail detection tool. Prioritize a usable detection workflow rather than high-confidence attack classification.

## Lab setup and execution

The same customer-managed `lab-attacker-policy` remained attached to the `lab-attacker` IAM user.

| Version | Lab permissions | State before attack |
|---|---|---|
| v2 | Includes `iam:ListUsers` (from Lab 1) | Nondefault |
| v3 | Allows `iam:SetDefaultPolicyVersion` on the lab policy; does not include `iam:ListUsers` | Default |

Using attacker CLI credentials, the user switched the default policy version from **v3 to v2**, then successfully ran `aws iam list-users --profile lab-attacker`.

**Confirmed outcome:** The user demonstrated that a principal allowed to change the default version of an attached customer-managed policy can activate an older version with broader permissions. Unlike Lab 1, the attack did **not** require creating a new policy version during the escalation.

**Evidence qualification:** The discussion confirmed that v3 was default before the switch and that `ListUsers` succeeded afterward. A fresh pre-switch `ListUsers` denial was not explicitly reported in this lab; don't claim one was observed.

## CloudTrail investigation

The user found a `SetDefaultPolicyVersion` event with:

```json
"requestParameters": {
  "policyArn": "<lab-attacker-policy ARN>",
  "versionId": "v2"
}
```

This identifies the policy and **newly requested default version**. The event itself **does not record the previous default version**; that was known from earlier lab state. The event was located and the live detection worked on a fresh export; the full event identity and error fields were not separately pasted into the conversation for independent revalidation.

## Detection engineering

The simple first-pass rule was:

```python
def detect_set_default_policy_version(df):
    events = find_events(df, event_name="SetDefaultPolicyVersion")
    alerts = events[events["errorCode"].isna()]
    return {
        "rule": "IAM_DEFAULT_POLICY_VERSION_CHANGED",
        "severity": "MEDIUM",
        "reason": "An existing IAM policy version was activated",
        "alerts": alerts,
    }
```

The user and assistant also redesigned the first `detect_create_policy_version()` rule to return the same dictionary shape: `rule`, `severity`, `reason`, and `alerts`. `report_detections()` consumes metadata from this structure, removing rule-specific hardcoding.

A **detector registry** reduces duplicate calls:

```python
detectors = [detect_create_policy_version, detect_set_default_policy_version]
for detector in detectors:
    report_detections(detector(df))
```

Functions are first-class Python values; this is a list of callables, conceptually similar to a function-pointer array.

**Implementation status:** The user reported that both rules yielded the expected detections on local CloudTrail data. The **updated combined Python script has not yet been supplied or pushed**. The existing [October 14 parser checkpoint](2026-10-14-cloudtrail_parser.py) represents Lab 1 only.

## Test results

| Test | Expected | User-reported observation |
|---|---|---|
| Recent JSON containing the Lab 2 `SetDefaultPolicyVersion` activity | Matching detection | Pass |
| Earlier JSON predating the Lab 2 event | No matching Lab 2 detection | Pass |

**Not tested:** A `SetDefaultPolicyVersion` event with `errorCode` present. The historical negative test establishes absence-of-target-event filtering, not failed-API filtering.

## Limits and scope decisions

- Successful `SetDefaultPolicyVersion` is a **candidate security event**, not proof of unauthorized privilege escalation.
- The rule is false-positive-prone: legitimate IAM maintenance uses the same API.
- Confirming permission expansion requires prior default version state and policy comparison; CloudTrail records the selected version, not the previous default.
- No IAM-state comparison, automated correlation, alert tuning, production notification, or regression-test suite was implemented.
- This intentional minimal scope keeps time available for the remaining IAM privilege-escalation techniques.

## Learning checkpoint

Lab 2 was materially faster than Lab 1: the user proposed the v3-to-v2 attack scenario, quickly located CloudTrail evidence, reused the parser and reporting flow, suggested detector metadata in a common return structure, and raised maintainability concerns about repetitive detector calls. The resulting detector registry is a useful reusable tool-engineering improvement.

**Next action:** Obtain the *exact latest working combined script* from the user and commit it as a separately versioned checkpoint; do not overwrite the existing Lab 1 source with an unverified reconstruction. Then proceed to the next distinct privilege-escalation case. Do not commit raw CloudTrail event histories, credentials, access keys, or IP addresses to the public repository.
