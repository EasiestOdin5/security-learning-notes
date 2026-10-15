# IAM Privilege Escalation Lab 05 — CreateLoginProfile

**Date:** 2026-10-15  
**Status:** API mechanism reproduced, AWS Console login confirmed, basic detector tested locally; detailed CloudTrail comparison pending  
**Reference:** [IAM privilege-escalation reference — case 5](2026-10-14-iam-privilege-escalation-reference.md)

## Objective

Independently study the AWS IAM `CreateLoginProfile` API using official AWS reference documentation, demonstrate that `lab-attacker` can create a console password for an existing IAM user without a login profile, and extend the established basic CloudTrail detection pattern without overengineering.

## Lab preparation and API learning

- Existing target: `lab-privileged`, created in Lab 4 with API access credentials. The user reported no preexisting console password; the successful `CreateLoginProfile` call supports that no login profile existed at execution time.
- Actor: `lab-attacker`, granted `iam:CreateLoginProfile` for the target IAM user.
- Learned the difference between `CreateLoginProfile` (initial console password) and `UpdateLoginProfile` (change an existing login profile).
- Used `aws iam create-login-profile --generate-cli-skeleton` to create a **local JSON template**. This does not make an API request.
- Filled in the user name, a password, and `PasswordResetRequired=false`; called the real API with `--cli-input-json file://create-login-profile.json --profile lab-attacker`.
- Resolved a Windows file-encoding problem: the JSON had been saved with UTF-16 encoding, causing AWS CLI `Invalid JSON received` and Python UTF-8 decoding failure (byte `0xff`). Converted the file to UTF-8 and the API call worked.
- **Security note:** The password appeared in the chat during debugging. Treat that value as exposed, rotate/remove the test password during cleanup, and never commit it.

## Observed outcome

The user successfully signed in as `lab-privileged` through the IAM-user AWS Management Console sign-in flow after `lab-attacker` created the login profile.

**No MFA challenge was presented for this login.** This establishes that MFA was not enforced for the observed session; it does not establish that IAM users universally lack MFA enforcement. IAM Identity Center and IAM-user authentication are distinct.

The action creates a console authentication method; it **does not change the target IAM user's permissions**. The attacker can potentially use whatever effective permissions the target has, subject to authentication/authorization controls.

## CloudTrail detector

Added (locally) a first-pass detector for successful `CreateLoginProfile` events. The proposed implementation returned the same metadata contract as the previous rules:

```python
def detect_create_login_profile(df):
    events = find_events(df, event_name="CreateLoginProfile")
    errors = events.get(
        "errorCode",
        pd.Series(index=events.index, dtype="object")
    )
    alerts = events[errors.isna()]
    return {
        "rule": "IAM_LOGIN_PROFILE_CREATED",
        "severity": "MEDIUM",
        "reason": "An IAM console login profile was successfully created",
        "alerts": alerts
    }
```

Registered the function in the existing detector list, according to the user-reported implementation. The user reported **positive and negative tests completed**. The exact fixture contents and console outputs were not supplied, so record this as user-tested, not independently verified. No additional filtering or formal test harness was added.

**Interpretation:** Detecting a successful `CreateLoginProfile` event is a candidate alert, **not proof of malicious intent or privilege escalation**.

## CloudTrail investigation status

Inspecting and correlating `CreateLoginProfile` with `ConsoleLogin` was recommended, but the conversation does **not** document a completed event-by-event comparison. Do not label this forensic step as completed.

## Learning outcome and deliberate scope

- Independently interpreted AWS API documentation and distinguished skeleton generation from an actual API request.
- Demonstrated how adding a login profile enables a new authentication route for an existing identity.
- Observed the interaction with missing MFA enforcement on this test user's session.
- Reused the existing Python detector/report interface without spending time on advanced detection tuning.
- Deferred shared missing-`errorCode` helper refactoring and additional detector engineering, as their learning value was low for this lab.

## Next actions

1. Optionally inspect `CreateLoginProfile` and `ConsoleLogin` events if completing the CloudTrail investigative checkpoint is desired.
2. Obtain the user's current four-detector Python source before committing the exact Lab 5 code; do not reconstruct it as if it were a verified user-uploaded artifact.
3. Clean up test login profile/password and unnecessary IAM permissions after retaining evidence; avoid committing real passwords, credentials, or raw CloudTrail data.
