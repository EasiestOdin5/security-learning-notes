# AWS Security Lab: GuardDuty Introduction and IAM Attack-Sequence Triage

**Session dates:** August 19–20, 2026  
**Status:** Introductory lab completed; GuardDuty intentionally remains enabled during its 30-day trial  
**Region:** `us-east-1` only  
**Environment:** Amazon GuardDuty, sample findings, attack sequences, finding JSON, usage metrics, and finding archival

---

## 1. Lab Scope

This was an introductory GuardDuty lab, not the planned deep incident-response capstone.

The goals were to:

1. Enable GuardDuty safely and understand its cost model.
2. Generate synthetic sample findings without deploying attack infrastructure.
3. Investigate one critical IAM credential-compromise sequence.
4. Separate GuardDuty conclusions from facts that require underlying evidence.
5. Choose an initial containment action.
6. Archive a reviewed finding and understand retention.
7. Leave GuardDuty enabled temporarily during the free trial.

A broader multi-finding GuardDuty capstone is deferred until the remaining AWS and Kubernetes fundamentals are complete.

---

## 2. Cost and Enablement

Before enablement, the GuardDuty Console showed that `us-east-1` was eligible for a 30-day free trial.

The enablement page explained that GuardDuty could analyze:

- CloudTrail management events
- VPC Flow Logs
- DNS query logs
- S3 data events
- EKS audit logs
- Lambda network activity
- RDS login activity
- EBS volume data for supported malware detection

Initial enablement automatically included the available protection plans except Runtime Monitoring and Malware Protection for S3. No EC2, EKS, RDS, Lambda, runtime agent, or malware-test workload was created for this lab.

The built-in sample-finding feature was used instead of the GuardDuty tester scripts. Sample findings use placeholder data and do not perform the depicted attacks.

### Cost conclusions

- Built-in sample findings do not have a separate per-finding charge.
- GuardDuty billing is based on real telemetry processed while the detector is enabled.
- Usage is regional and can be stopped by disabling GuardDuty in that Region.
- Closing the browser, deleting findings, or archiving findings does not stop monitoring.
- Suspending retains configuration/findings; disabling removes the detector and findings.
- GuardDuty remains enabled in `us-east-1` during the confirmed trial.

The Usage page initially showed no data. Later, only CloudTrail-event usage appeared, which was consistent with a quiet personal account and no applicable workloads.

---

## 3. Sample Findings

The Console successfully generated GuardDuty sample findings. One critical finding was selected:

```text
AttackSequence:IAM/CompromisedCredentials
```

The sample title described a potential credential compromise of a placeholder IAM user called `john_doe`.

The attack sequence contained four displayed signals:

1. `CreateRole` from an IP classified as a Tor exit node.
2. `DeleteTrail` from a client fingerprinted as Kali Linux.
3. `AttachRolePolicy` from a client fingerprinted as Kali Linux.
4. A CloudTrail trail becoming disabled/deleted.

The sequence-level indicators additionally referenced `ListUsers` and mapped the activity to MITRE ATT&CK tactics and techniques including:

- Initial Access
- Discovery
- Persistence
- Privilege Escalation
- Defense Evasion
- Valid Accounts: Cloud Accounts
- Cloud Account Discovery
- Account Manipulation
- Additional Cloud Roles
- Impair Defenses: Disable or Modify Cloud Logs

---

## 4. Initial Interpretation

The initial interpretation was substantially correct:

- The placeholder identity was likely compromised.
- The requests appeared to use Tor and a Kali Linux client.
- Creating a role could establish persistence.
- Attaching a role policy could grant additional capability.
- Deleting the trail attempted to reduce audit visibility.

### Correction: role versus policy

The attacker did not “attach a role.” The sequence showed:

```text
CreateRole
→ create a role

AttachRolePolicy
→ attach a managed policy to a role
```

The GuardDuty JSON did not provide the created role name or attached policy ARN. Therefore, the alert alone could not prove exactly what privileges were gained.

---

## 5. Tor and Kali Interpretation

The likely intended path was:

```text
Kali client
→ Tor network
→ Tor exit address
→ AWS API endpoint
```

GuardDuty could infer:

- Tor usage from threat-intelligence classification of the observed source address.
- Kali Linux from a client or user-agent fingerprint.

GuardDuty could not see the attacker’s original address behind Tor or prove the attacker’s physical location. The shared credential, endpoint, and timestamps caused the signals to be correlated, but the topology remained an inference.

The sample IP, access-key value, user, geolocation, and other attack artifacts were placeholders.

---

## 6. Temporary Credential Detail

The sample credential ID began with:

```text
ASIA...
```

This indicates an AWS temporary STS credential rather than a normal long-term IAM-user access key, which typically begins with `AKIA`.

The sample also showed MFA enabled for the session. This did not prove that the later API actions were legitimate. A temporary credential set can be stolen after a valid MFA-authenticated session is created.

### Containment implication

Changing the IAM user’s password alone would not necessarily invalidate an already-issued temporary session.

The immediate identity containment action would be:

> Revoke the compromised active session credentials.

AWS treats the temporary access key, secret key, and session token as one credential set. The session token is not individually reset or rotated. Active sessions can be revoked, and the source user’s password, long-term access keys, and MFA configuration should also be reviewed so that new sessions cannot be created.

---

## 7. `DeleteTrail` Clarification

`DeleteTrail` deletes a trail’s configuration and stops future delivery by that trail.

It does not automatically:

- Delete existing CloudTrail log objects from S3.
- Remove the `DeleteTrail` management event.
- Eliminate the built-in CloudTrail Event History.
- Disable every possible trail or organization-level logging source.

The attacker would need separate S3 permissions such as `s3:DeleteObject` to erase previously delivered log files.

`StopLogging` and `DeleteTrail` are also different:

- `StopLogging` stops delivery while retaining the trail configuration.
- `DeleteTrail` removes the trail configuration.

In this sample, “`DeleteTrail` invoked” and “trail logging disabled” appeared as an API-oriented signal and a derived impact signal. They did not necessarily represent two separate attacker commands.

---

## 8. GuardDuty Alert Versus Evidence

GuardDuty provided a correlated security story, but it did not contain every fact needed for a complete investigation.

In a real incident, CloudTrail would be used to determine:

- Exact request time
- Caller identity and session context
- Source IP
- User agent
- Created role name
- Trust policy supplied to `CreateRole`
- Policy ARN supplied to `AttachRolePolicy`
- Trail name supplied to `DeleteTrail`
- Other APIs called by the same credential before and after the alert

Other evidence could include identity-provider logs, organization-level trails, protected S3 log storage, VPC/DNS telemetry, and workload logs.

Because this was a sample finding, the depicted `CreateRole`, `AttachRolePolicy`, `ListUsers`, and `DeleteTrail` calls were not expected to appear in the account’s real CloudTrail Event History.

### Core model

```text
GuardDuty finding
→ suspicious interpretation and prioritization

Underlying telemetry
→ proof, full scope, timeline, and response evidence
```

---

## 9. Incident Response Outline

For a real version of this finding, the response order would be:

1. Preserve available evidence and record the finding.
2. Revoke the compromised temporary session credentials.
3. Prevent the source identity from creating new sessions.
4. Inspect the created role, trust policy, attached policies, and related resources.
5. Quarantine or remove attacker-created persistence after recording it.
6. Restore the deleted trail and verify other logging remains intact.
7. Search CloudTrail and other telemetry for all activity by the credential, principal, IP, and user agent.
8. Determine whether other identities, Regions, services, or accounts were affected.
9. Rotate or reset source credentials and validate MFA.
10. Document eradication, recovery, and preventive-control changes.

The first containment decision was correctly identified as the suspicious credential/session rather than CloudTrail or the created role, because stopping the actor prevents additional changes.

---

## 10. Finding Lifecycle and SIEM Integration

The sample finding was manually archived.

Archiving:

- Moves it out of the Current findings view.
- Does not remediate the affected resource.
- Does not stop GuardDuty monitoring.
- Does not provide indefinite retention.

Archived findings can be viewed from:

```text
Findings → Archived
```

GuardDuty retains findings for 90 days. Production environments commonly forward findings through EventBridge or Security Hub to a SIEM/SOAR or export them to durable storage.

A common architecture is:

```text
GuardDuty
→ EventBridge or Security Hub
→ SIEM / SOAR / case-management workflow
```

The SIEM should also contain the underlying evidence sources, not only the GuardDuty alert.

---

## 11. Questions and Answers

### Q1. Does generating built-in sample findings normally cost extra?

**Answer:** No separate per-finding charge is expected. Normal GuardDuty telemetry-processing charges still apply outside a trial.

### Q2. Can GuardDuty be enabled briefly after the trial and billed proportionally?

**Answer:** Yes. GuardDuty is usage-based. A short test in a quiet account should be inexpensive, but actual cost depends on processed telemetry rather than only elapsed time.

### Q3. What AWS product costs roughly $3,000 per month?

**Answer:** AWS Shield Advanced, not GuardDuty.

### Q4. Does GuardDuty have to be disabled as a whole to stop monitoring charges?

**Answer:** Yes, in the relevant Region. Closing the Console or archiving findings does not stop analysis.

### Q5. What did the critical sample finding indicate?

**Answer:** A likely compromised cloud identity using suspicious network/client indicators to perform discovery, establish role-based persistence or escalation, and impair CloudTrail logging.

### Q6. Was Kali definitely located “behind” Tor?

**Answer:** That is the likely intended scenario, but GuardDuty only observes the exit address and client indicators; it does not see the attacker’s original address behind Tor.

### Q7. Did the attacker attach a role?

**Answer:** No. The sequence showed creation of a role and attachment of a policy to a role.

### Q8. Does `DeleteTrail` delete existing CloudTrail log files?

**Answer:** No. It deletes the trail configuration and stops future delivery for that trail. Existing S3 objects require separate deletion permissions.

### Q9. Does `DeleteTrail` completely disable CloudTrail?

**Answer:** No. It affects the targeted trail. Event History and other trails or organization-level logging may still provide visibility.

### Q10. Would changing the IAM user’s password invalidate the stolen `ASIA` credential immediately?

**Answer:** Not necessarily. The active temporary session must be revoked or allowed to expire; source credentials must also be secured to prevent new sessions.

### Q11. Should the response be described as “reset the session token”?

**Answer:** The better wording is “revoke the compromised active session credentials.” The temporary credential set works as a unit.

### Q12. Would the sample APIs appear in the account’s actual CloudTrail logs?

**Answer:** No. Sample findings are synthetic and do not execute the depicted APIs.

### Q13. Should GuardDuty findings be sent to a SIEM?

**Answer:** Yes, commonly through EventBridge or Security Hub, alongside the underlying cloud and identity telemetry.

### Q14. Where do archived findings go?

**Answer:** They remain under GuardDuty’s Archived findings view for the 90-day retention period.

### Q15. Can GuardDuty remain enabled through the free trial?

**Answer:** Yes. It remains enabled intentionally in `us-east-1`; usage and trial expiration must be monitored.

---

## 12. What Was Demonstrated

- Enabled GuardDuty in one Region after verifying trial eligibility.
- Reviewed protection-plan and telemetry sources.
- Checked the Usage page before and after telemetry appeared.
- Generated safe built-in sample findings.
- Selected and investigated a critical attack-sequence finding.
- Read the structured JSON and identified sample metadata.
- Distinguished alert inference from evidence requirements.
- Corrected role/policy terminology.
- Identified an `ASIA` temporary credential and its containment implications.
- Explained Tor exit visibility and Kali fingerprinting limitations.
- Distinguished trail configuration deletion from log-object deletion.
- Correctly prioritized session containment.
- Archived a finding and located the Archived view.
- Connected GuardDuty findings to SIEM and CloudTrail workflows.

---

## 13. Limitations and Deferred Work

The lab was guided and investigated only one synthetic attack sequence. It did not:

- Investigate a real finding.
- Pivot into matching real CloudTrail events.
- Configure EventBridge, Security Hub, SIEM forwarding, or automated containment.
- Export findings to S3.
- Review EC2, S3, malware, EKS, RDS, or Lambda cases.
- Demonstrate organization-wide GuardDuty administration.

A deeper multi-case GuardDuty capstone is intentionally deferred until the remaining fundamentals are complete.

---

## 14. Current AWS State and Follow-Up

GuardDuty remains enabled in `us-east-1` during its 30-day free trial.

Current follow-up obligation:

- Monitor GuardDuty Usage.
- Do not enable Runtime Monitoring, S3 Malware Protection, or on-demand malware scans for this introductory environment.
- Before the trial expires, either disable GuardDuty or consciously accept continuing usage charges.
- Return later for the deeper GuardDuty capstone.

The next fundamentals lab is **AWS Config and Security Hub**.
