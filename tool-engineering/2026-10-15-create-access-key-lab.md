# IAM Privilege Escalation Lab 04 — CreateAccessKey

**Date documented:** 2026-10-15  
**Status:** Attack reproduced; CloudTrail credential correlation confirmed; basic detector locally tested; latest code not committed  
**Reference:** [IAM privilege-escalation reference — case 4](2026-10-14-iam-privilege-escalation-reference.md)

## Scope and objective

Skipped case 3 for now because it involves multiple APIs. In case 4, demonstrate that an IAM principal permitted to call `iam:CreateAccessKey` for another IAM user can generate credentials for that user, authenticate with the new credentials, and use permissions that the original principal lacks.

## Controlled lab setup and observed results

- **Actor:** `lab-attacker`, granted `iam:CreateAccessKey` on the target IAM user (the exact resource scope of the attached lab policy was not verified in the conversation).
- **Target user:** `lab-privileged`, an IAM user that could perform `iam:ListUsers` but did not need AdministratorAccess.
- **Original target credentials:** CLI profile `lab-privileged`.
- **Newly created target credentials:** `lab-attacker` created a second access key for `lab-privileged`; the user configured those credentials as CLI profile `lab-privileged-compromised`.
- **Outcome:** `aws iam list-users --profile lab-privileged-compromised` succeeded, while `aws iam list-users --profile lab-attacker` returned `AccessDenied`.

**Conclusion:** Credential creation for another identity and subsequent use of that identity's greater effective privileges were demonstrated. The original `lab-attacker` user itself did not receive new permissions; the attacker obtained a different IAM user's credentials.

## CloudTrail investigation

1. Found the `CreateAccessKey` event where `userIdentity` represented `lab-attacker` and the target IAM user was `lab-privileged`.
2. Identified the **new key's ID** at `responseElements.accessKey.accessKeyId`; do not confuse it with `userIdentity.accessKeyId` in the same event, which is the **attacker's original calling credential**.
3. Located a subsequent successful `ListUsers` event under `lab-privileged` whose `userIdentity.accessKeyId` **matched the key created in step 2**.
4. Also verified `ListUsers` activity under `lab-privileged` using two different access key IDs; the same user ARN may therefore appear with distinct key IDs.

The match between `CreateAccessKey.responseElements.accessKey.accessKeyId` and later `ListUsers.userIdentity.accessKeyId` is the key forensic link between creation and use. Only key **IDs** were used for correlation; secret key material must never enter repository documentation.

## Detection implementation and tests

The chosen minimal rule flags successful `CreateAccessKey` events, without trying to confirm compromise or automatically correlate subsequent API calls:

```python
def detect_create_access_key(df):
    events = find_events(df, event_name="CreateAccessKey")
    alerts = events[events["errorCode"].isna()]
    return {
        "rule": "IAM_ACCESS_KEY_CREATED",
        "severity": "MEDIUM",
        "reason": "An IAM access key was successfully created",
        "alerts": alerts,
    }
```

**User-reported test:** Running the rule on fresh CloudTrail data produced **two detections**:
- `lab-admin` creating a key for `lab-privileged` as part of lab preparation.
- `lab-attacker` creating a key for `lab-privileged` as the simulated credential-compromise action.

Both are expected matches for this simple event-based rule. The first demonstrates a plausible **false positive** if all matches are interpreted as attacks. The rule does not determine whether the caller was authorized. A failed-`CreateAccessKey` negative test was **not** reported.

**Reporting enhancement proposed but not confirmed implemented:** Include `requestParameters.userName` (target user) and `responseElements.accessKey.accessKeyId` (created key ID). Avoid outputting `secretAccessKey`.

## CLI tool improvements discussed

The parser originally accepted only a positional CloudTrail JSON filename and ran all detectors automatically. A revised CLI interface was discussed and a full updated code example provided:
- `--detect`: run registered detectors.
- `--event CreateAccessKey`: show a targeted event view.
- Both flags may be combined.

The user initially reported `--detect` not working with a downloaded version, then received a complete replacement example. **Successful validation of that exact CLI revision was not explicitly confirmed** in the transcript. Do not claim the latest CLI file or three-detector code has been pushed; the last verified GitHub Python checkpoint remains [2026-10-14-cloudtrail_parser-lab2.py](2026-10-14-cloudtrail_parser-lab2.py).

## Limits and next step

- A successful `CreateAccessKey` is **not inherently malicious**. This is an intentionally broad candidate-event detector.
- The manual CloudTrail correlation is stronger evidence of misuse; it has **not** been built into the detection logic.
- Two access keys can be active for one IAM user, and their CloudTrail `accessKeyId` fields distinguish the credentials.
- No automated regression suite, negative failed-API test, or detection tuning was added in this lab.
- **Next:** Obtain the user's latest working Python source, verify the integrated Lab 4 detector and CLI handling, then commit a new dated source checkpoint. Continue to the next selected IAM privilege-escalation technique.

**Security housekeeping:** Delete the extra compromised test access key and remove unnecessary `iam:CreateAccessKey` permissions after collecting evidence. Do not commit raw CloudTrail logs, account IDs, source IPs, key IDs, or secret keys.
