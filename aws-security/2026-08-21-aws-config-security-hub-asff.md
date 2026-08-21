# AWS Config, Security Hub CSPM, and ASFF Lab

**Date:** August 21, 2026  
**Region:** `us-east-1`  
**Lab type:** Guided, hands-on  
**Safety note:** Account IDs, ARNs, access-key examples, IP addresses, finding IDs, detector IDs, and resource IDs are omitted.

## Objectives

- Detect an insecure Security Group configuration with AWS Config.
- Observe the configuration before and after remediation.
- Understand how Security Hub CSPM turns control results into standardized findings.
- Compare a Config-backed compliance finding with a GuardDuty threat finding.
- Follow a finding from detection through remediation and resolution.
- Keep the experiment inexpensive and clean up paid resources.

## Core mental model

| Service | Primary job | Example from this lab |
|---|---|---|
| AWS Config | Records resource configuration and evaluates compliance | Detected SSH open to the internet |
| GuardDuty | Detects potentially malicious behavior | Produced a synthetic EKS compromise attack sequence |
| Security Hub CSPM | Evaluates security controls and centralizes normalized findings | Displayed both Config-backed and GuardDuty findings |
| ASFF | Common finding format used by Security Hub | Standardized severity, workflow, compliance, resource, and source fields |

Security Hub centralizes and organizes security findings. It does not replace the source services or automatically fix resources.

## Lab setup

AWS Config was configured to:

- Record only `AWS::EC2::SecurityGroup`.
- Use continuous recording.
- Use the AWS Config service-linked role.
- Deliver configuration history to a dedicated S3 bucket.
- Evaluate the AWS managed rule `restricted-ssh`.

Limiting the recorder to one resource type kept the lab focused and reduced potential Config charges.

## Deliberate misconfiguration

An unattached test Security Group named `config-lab-open-ssh` was created in the default VPC with this inbound rule:

- Protocol: TCP
- Port: 22
- Source: `0.0.0.0/0`

AWS allowed the Security Group to be created. AWS Config then evaluated it as **NON_COMPLIANT**.

This demonstrates a detective control:

```text
Configuration change
        ↓
AWS Config records and evaluates it
        ↓
NON_COMPLIANT result
        ↓
Human or automation remediates it
```

AWS Config did not prevent the change. Prevention would require a separate control such as IAM, an SCP, a permissions boundary, or a deployment-policy gate. Config can initiate automated remediation, but that occurs after detection.

## Configuration history

After the SSH rule was removed, the Config timeline showed the material difference:

```text
Before: ipPermissions contained TCP/22 from 0.0.0.0/0
After:  ipPermissions was empty
```

The history also preserved capture times, resource state, and the relationship to the VPC. This answers two important investigation questions:

1. What does the resource look like now?
2. What did it look like before the change?

## Security Hub CSPM

Security Hub was enabled for this standalone account without configuring an Organizations delegated administrator or trusted access.

The automatically enabled standards included:

- AWS Foundational Security Best Practices v1.0.0
- CIS AWS Foundations Benchmark v1.2.0

The relevant control was:

- **Control:** EC2.13
- **Requirement:** Security Groups should not allow `0.0.0.0/0` or `::/0` access to port 22.
- **Severity:** High
- **Resource:** EC2 Security Group
- **Evaluation source:** AWS Config rule `restricted-ssh`

Important correction: EC2.13 belongs to **CIS AWS Foundations Benchmark v1.2.0, requirement 4.1**. It is not an AWS Foundational Security Best Practices control.

The detailed checks showed:

- Default Security Groups: `PASSED / RESOLVED`
- The deliberately insecure test group: `FAILED / NEW`

The aggregate summary briefly showed stale or empty data even though the detailed check had updated. This was a console aggregation delay, not evidence that the control failed.

## ASFF comparison

The failed EC2.13 finding exposed these normalized fields:

| Field | Value |
|---|---|
| `SchemaVersion` | `2018-10-08` |
| `Severity.Label` | `HIGH` |
| `Compliance.Status` | `FAILED` |
| `Workflow.Status` | `NEW` |

GuardDuty sample findings were generated again after Security Hub was enabled. The GuardDuty integration then delivered a synthetic EKS attack-sequence finding to Security Hub.

| Field | Config-backed finding | GuardDuty finding |
|---|---|---|
| Schema | ASFF `2018-10-08` | ASFF `2018-10-08` |
| Source | Security Hub CSPM / Config control | GuardDuty |
| Meaning | Configuration violates a security control | Behavior resembles an attack sequence |
| Severity observed | High | Critical |
| Example type | EC2.13 compliance check | `TTPs/AttackSequence:EKS/CompromisedCluster` |
| Main response | Correct the configuration | Investigate and contain possible compromise |

The common schema makes it easier for a SIEM, SOAR platform, ticketing system, or analyst workflow to process findings from different sources.

## Workflow status

The GuardDuty sample finding was changed from `NEW` to `NOTIFIED`.

`NOTIFIED` is only a workflow label. It does not send an email by itself. A real notification path would be:

```text
Security Hub finding
        ↓
Amazon EventBridge rule
        ↓
SNS, email, ticketing system, SIEM, or SOAR
```

## Remediation lifecycle

The open SSH rule was removed and AWS Config was re-evaluated.

Observed result:

```text
Security Group fixed
        ↓
AWS Config: COMPLIANT
        ↓
Security Hub EC2.13: PASSED / RESOLVED
```

Security Hub did not perform the remediation. The configuration was corrected manually, Config detected the corrected state, and Security Hub updated the finding.

## Cleanup and continuing state

Completed:

- Deleted the test Security Group.
- Deleted the Config rule.
- Stopped the Config recorder.
- Emptied the Config delivery bucket.

Verify separately that the empty S3 bucket itself has been deleted if it is no longer wanted.

Intentionally continuing during confirmed trials:

- GuardDuty in one Region.
- Security Hub in one Region.

Disabling a service does not pause and preserve unused days of a trial; the trial window continues from initial activation.

## Questions and answers

### Is AWS Config detection-based?

Yes, primarily. It records configuration state and evaluates compliance. It can trigger remediation, but it normally detects the change after it occurs.

### Are Config detections pushed to GuardDuty?

No. GuardDuty focuses on potentially malicious activity. Security Hub is the place where findings from GuardDuty and configuration/control results can be centralized.

### Does Security Hub copy every source finding unchanged?

No. Security Hub normalizes findings into AWS Security Finding Format while retaining source-specific details. Security Hub controls can use Config evaluations to produce standardized compliance findings.

### What does `FAILED / NEW` mean?

The resource currently fails the control and the finding has not yet moved through the analyst workflow.

### What does `PASSED / RESOLVED` mean?

The latest evaluation passed and the previously active failure is no longer open.

### Does setting a finding to `NOTIFIED` send email?

No. It records workflow state. EventBridge plus a destination such as SNS is required for an actual notification.

### Why did the Security Hub summary initially show no data?

Newly enabled controls and integrations need time to evaluate resources, ingest findings, and update aggregate widgets. Detailed checks can become current before summary widgets.

### Do GuardDuty sample findings reach Security Hub?

Yes, when the integration is connected and the samples are generated after Security Hub is enabled. They remain synthetic findings, not proof of activity in the account.

### Is a tiny S3 bucket expensive?

Usually not. Charges come from storage, requests, and transfer rather than merely naming a bucket. Tiny lab data is generally negligible, but unused buckets and objects should still be cleaned up.

### How much web-attack knowledge is needed for the current goal?

Practical working knowledge is sufficient initially: HTTP, sessions and tokens, access control, injection, XSS, SSRF, path traversal, file upload, command injection, insecure deserialization, API authorization, and tracing requests into cloud telemetry. Advanced browser exploitation and zero-day research are not immediate priorities.

## Key takeaways

1. AWS Config answers what a resource looks like, whether it complies, and how it changed.
2. GuardDuty looks for behavior suggesting malicious activity.
3. Security Hub CSPM provides controls, aggregation, workflow, and a common finding format.
4. A detective control can identify a bad state without preventing its creation.
5. ASFF lets different sources share standardized fields while preserving their distinct meanings.
6. A complete control lifecycle is: create condition, detect, investigate, remediate, re-evaluate, and resolve.
7. Finding status is not notification or remediation automation.

## References

- [AWS Config pricing](https://aws.amazon.com/config/pricing/)
- [AWS Security Hub pricing](https://aws.amazon.com/security-hub/pricing/)
- [Security Hub EC2 controls](https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html)
- [Enabling Security Hub standards](https://docs.aws.amazon.com/securityhub/latest/userguide/enable-standards.html)
- [AWS Security Finding Format](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-format.html)
- [Viewing Security Hub findings and JSON](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-viewing.html)
- [GuardDuty integration with Security Hub](https://docs.aws.amazon.com/guardduty/latest/ug/securityhub-integration.html)
- [Security Hub internal providers](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-internal-providers.html)
