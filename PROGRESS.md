# Security Skills Progress Tracker

**Baseline date:** August 11, 2026  
**Last updated:** August 19, 2026  
**Scale:** 0–10, where 10 represents strong specialist-level working knowledge  
**Scoring policy:** Scores change only when dated notes contain demonstrated evidence. Discussion, recognition, or a correct guess alone does not increase a score.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Remaining gap |
|---|---:|---:|---:|---:|---:|
| Modern Identity | 4.0 | 5.25 | 8.0 | +1.25 | 2.75 |
| AWS / Cloud Security | 5.0 | 6.25 | 8.0 | +1.25 | 1.75 |
| Kubernetes Security | 5.0 | 5.0 | 8.0 | — | 3.0 |
| Cloud / Modern Incident Response | 6.0 | 7.0 | 8.0 | +1.0 | 1.0 |
| DevSecOps / CI-CD Security | 5.5 | 5.5 | 7.5 | — | 2.0 |
| Application Security | 6.0 | 6.0 | 7.5 | — | 1.5 |
| PKI / TLS / Secrets | 4.5 | 4.5 | 7.0 | — | 2.5 |
| Linux Security Operations | 6.0 | 6.0 | 7.0 | — | 1.0 |
| Vulnerability Management | 5.0 | 5.0 | 7.0 | — | 2.0 |
| Enterprise Security Controls | 5.5 | 6.5 | 7.0 | +1.0 | 0.5 |

## Radar View: Initial, Current, and Goal

![Security skills radar showing baseline, current evidence, and goal](assets/security-skills-radar.svg)

The chart uses the same 0–10 evidence-based scores as the table. Moving outward means stronger demonstrated working knowledge; it does **not** mean percent completion of a fixed course.

### Overall interpretation

The strongest measured improvement so far is in **Modern Identity** and **AWS / Cloud Security**, with supporting gains in **Cloud / Modern Incident Response** and **Enterprise Security Controls**. The advanced IAM lab added direct evidence for boundary evaluation, request conditions, trust-policy conditions, `PassRole`, and successful/denied STS and EC2 reconstruction. The improvement is real but still guided; independent transfer to a new authorization scenario remains the main requirement for larger increases.

No score was increased for Kubernetes, DevSecOps, AppSec, PKI/TLS/secrets, Linux operations, or vulnerability management because the current repository does not yet contain new dated evidence for those areas.

---

## Initial Matrix

This is the fixed August 2026 assessment baseline. It should never be rewritten to match later ability.

| Skill area | Initial score | Baseline interpretation |
|---|---:|---|
| Modern Identity | 4.0 | Security awareness present; architecture and operational mechanics needed development |
| AWS / Cloud Security | 5.0 | Familiar with major services and threats; needed stronger independent configuration and troubleshooting |
| Kubernetes Security | 5.0 | Conceptual familiarity; limited hands-on operational evidence |
| Cloud / Modern Incident Response | 6.0 | Existing investigation strength; needed deeper cloud-native telemetry and identity reconstruction |
| DevSecOps / CI-CD Security | 5.5 | Familiar with tools and pipeline concepts; needed an end-to-end practical workflow |
| Application Security | 6.0 | Strong attack reasoning; defensive source-to-sink method needed more consistent demonstration |
| PKI / TLS / Secrets | 4.5 | Lower-confidence estimate; needed practical identity, certificate, and secrets-management work |
| Linux Security Operations | 6.0 | Useful operational foundation; needed more cloud/container-oriented repetition |
| Vulnerability Management | 5.0 | Familiar with scanning concepts; prioritization and remediation workflow needed more evidence |
| Enterprise Security Controls | 5.5 | General security-controls knowledge; cloud policy evaluation and governance needed deeper practice |

---

## Goal Matrix

| Skill area | Goal | What reaching the goal should mean |
|---|---:|---|
| Modern Identity | 8.0 | Independently explain, configure, troubleshoot, and investigate human and workload identity flows |
| AWS / Cloud Security | 8.0 | Independently secure and investigate common AWS architectures, identity, networking, data, and telemetry |
| Kubernetes Security | 8.0 | Independently reason about workload identity, RBAC, network policy, runtime controls, nodes, and control plane exposure |
| Cloud / Modern Incident Response | 8.0 | Reconstruct cloud incidents across identity, control plane, workload, and network telemetry |
| DevSecOps / CI-CD Security | 7.5 | Build and operate a practical secure pipeline with findings triage and remediation |
| Application Security | 7.5 | Trace vulnerabilities systematically from source through transforms to sink and propose robust fixes |
| PKI / TLS / Secrets | 7.0 | Confidently operate certificate, TLS, key, token, and secrets-management workflows |
| Linux Security Operations | 7.0 | Independently investigate, harden, and troubleshoot Linux systems used in modern workloads |
| Vulnerability Management | 7.0 | Prioritize, validate, assign, remediate, and verify vulnerabilities as an operational program |
| Enterprise Security Controls | 7.0 | Map policy, preventive controls, detective controls, governance, and evidence across enterprise environments |

---

## Daily Evidence and Score History

### August 11, 2026 — Baseline assessment

**Evidence type:** Diagnostic questions, prior experience, and self-report.

This established the initial matrix. The strongest demonstrated areas were detection/SIEM, endpoint and Windows security, malware/offensive reasoning, security investigation, and AI/SOC automation. The main modernization priorities were cloud identity, AWS security, Kubernetes security, cloud-native incident response, and DevSecOps.

**Score changes:** None. This is the baseline.

---

### August 14–15, 2026 — AWS SSO, CLI, IAM, and CloudTrail

**Evidence:** [AWS Security Lab: SSO, CLI, IAM, and CloudTrail](aws-security/2026-08-14-15-aws-sso-cli-cloudtrail.md)

Demonstrated hands-on:

- Created and used IAM Identity Center account assignments and permission sets.
- Distinguished an Identity Center user, permission set, generated IAM role, and STS assumed-role session.
- Configured AWS CLI SSO and completed browser authorization.
- Verified the active principal with `aws sts get-caller-identity`.
- Used temporary credentials rather than permanent IAM-user access keys.
- Tested an expected read-only authorization failure.
- Compared Console and CLI activity in CloudTrail.
- Used role, session, source IP, user agent, event name, and error fields for attribution.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Modern Identity | 4.0 | 4.5 | Direct Identity Center, SSO, permission-set, assumed-role, and temporary-session evidence |
| AWS / Cloud Security | 5.0 | 5.25 | Practical IAM, VPC navigation, authorization testing, and CloudTrail use |

**Why the increase was limited:** The workflow was completed with guidance, and independent reconstruction of token/session behavior still needs repetition.

---

### August 16, 2026 — Explicit Deny, EC2 Networking, and Flow Logs

**Evidence:** [AWS Security Lab: Explicit Deny, EC2 Networking, CloudTrail, and VPC Flow Logs](aws-security/2026-08-16-aws-network-security-cloudtrail-flow-logs.md)

Demonstrated hands-on:

- Combined `AdministratorAccess` with an inline explicit deny and observed deny precedence.
- Distinguished public/private subnet routing from public/private IP addressing.
- Launched Amazon Linux in the intended VPC and public subnet.
- Restricted inbound SSH to one `/32` source.
- Corrected Windows OpenSSH private-key permissions.
- Created and associated a dedicated custom NACL.
- Broke SSH by denying outbound ephemeral traffic, then restored it.
- Removed SG outbound rules and confirmed stateful SSH replies still worked.
- Demonstrated that an EC2-initiated HTTPS request required separate SG egress.
- Identified the NACL as the remaining blocker after SG egress was restored.
- Reconstructed `CreateNetworkAclEntry` activity in CloudTrail.
- Connected `lab-admin`, the `AWSReservedSSO_AdministratorAccess` role, the session ARN, source IP, direction, rule number, action, and port range.
- Created subnet VPC Flow Logs and delivered them to CloudWatch Logs.
- Filtered real `REJECT` records and identified ICMP from protocol `1` and ports `0 0`.
- Cleaned up EC2, logging, IAM-role, NACL, SG, and key-pair resources.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| AWS / Cloud Security | 5.25 | 5.5 | Direct configuration and failure testing across routing, SGs, NACLs, EC2, CloudTrail, and Flow Logs |
| Cloud / Modern Incident Response | 6.0 | 6.25 | Reconstructed real control-plane identity evidence and network `ACCEPT`/`REJECT` telemetry |
| Enterprise Security Controls | 5.5 | 5.75 | Demonstrated explicit-deny precedence and layered preventive/detective controls |

**Why the increase was limited:** The lab showed practical understanding, but the complete bidirectional rule set was not initially reconstructed without prompting. Independent repetition is required before another material increase.

---

### August 17–18, 2026 — EC2 IAM Role, IMDSv2, and CloudTrail

**Evidence:** [AWS Security Lab: EC2 IAM Role, IMDSv2, Least Privilege, and CloudTrail](aws-security/2026-08-17-18-ec2-iam-role-imdsv2-cloudtrail.md)

Demonstrated hands-on:

- Created an IAM role trusted by the EC2 service and separated its trust policy from its permissions policy.
- Added a least-privilege inline policy allowing only `s3:ListAllMyBuckets`.
- Attached the role to Amazon Linux through an EC2 instance profile.
- Required IMDSv2 and obtained a token without displaying it.
- Retrieved the attached role name and inspected non-secret credential metadata.
- Proved tokenless IMDS access returned `401 Unauthorized`.
- Verified the EC2 assumed-role identity with `sts:GetCallerIdentity`.
- Performed an allowed `ListBuckets` call and a denied `DescribeInstances` call.
- Diagnosed a malformed regional prefix-list selection and a failed SSH connection caused by the default Security Group being attached.
- Corrected the instance ENI's Security Group and connected with browser-based EC2 Instance Connect.
- Reconstructed allowed and denied workload activity in CloudTrail.
- Correlated assumed-role identity, instance session name, source IP, API action, error, and `ec2RoleDelivery: 2.0`.
- Corrected the assumption that EC2 temporary credentials are bound to the original instance; recognized that stolen credentials are portable until expiration but cannot refresh after instance access is lost.
- Cleaned up the instance, dedicated Security Group, role, and inline policy.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Modern Identity | 4.5 | 4.75 | Direct workload-role, trust-policy, assumed-session, IMDSv2, expiration, and refresh evidence |
| AWS / Cloud Security | 5.5 | 5.75 | Practical role, instance profile, EC2, managed prefix list, least privilege, metadata, and troubleshooting evidence |
| Cloud / Modern Incident Response | 6.25 | 6.5 | Reconstructed both allowed and denied workload events using identity, network, and credential-delivery context |
| Enterprise Security Controls | 5.75 | 6.0 | Demonstrated layered trust, permissions, network-source restriction, IMDSv2, and least-privilege controls |

**Why the increases were limited:** The workflow was guided. The role and CloudTrail chain were reconstructed successfully, but credential portability was initially answered incorrectly, and several console/configuration steps required troubleshooting prompts. The next increase should require independent repetition or transfer to a new workload scenario.

---

### August 18, 2026 — S3 Authorization, Versioning, and CloudTrail Data Events

**Evidence:** [AWS Security Lab: S3 Authorization, Versioning, and CloudTrail Data Events](aws-security/2026-08-18-s3-authorization-versioning-cloudtrail-data-events.md)

Demonstrated hands-on:

- Created a private S3 bucket with Block Public Access enabled and separated objects into `allowed/` and `restricted/` prefixes.
- Created and assumed a scoped IAM Identity Center permission set through an AWS CLI SSO profile.
- Allowed bucket listing only for one prefix and object reads only within that prefix.
- Verified allowed operations and implicit-deny failures against the restricted prefix.
- Applied a bucket-policy explicit deny and proved it overrode the identity-policy allow without denying the separate list action.
- Observed Block Public Access reject a bucket policy that attempted to grant public object access.
- Inspected default SSE-S3 encryption without claiming customer-managed KMS experience.
- Enabled versioning, distinguished the pre-versioning `null` version from a generated version ID, and added `s3:GetObjectVersion` to retrieve historical data.
- Created a delete marker and recovered the object by removing only that marker.
- Distinguished CloudTrail management events from S3 object-level data events.
- Created a narrowly filtered trail for read-only `GetObject` events and parsed both successful and denied events from delivered JSON.
- Attributed object access to the `AWSReservedSSO_S3LabScopedRead` assumed role using event identity, resource, source-IP, user-agent, and error fields.
- Removed the trail, buckets, versions, permission-set assignment, and permission set.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Modern Identity | 4.75 | 5.0 | Used a second scoped Identity Center role and correlated its assumed-role session to data-plane activity |
| AWS / Cloud Security | 5.75 | 6.0 | Demonstrated S3 authorization, resource policies, explicit deny, Block Public Access, encryption inspection, and version recovery |
| Cloud / Modern Incident Response | 6.5 | 6.75 | Configured object-level telemetry and reconstructed successful and denied access from raw CloudTrail JSON |
| Enterprise Security Controls | 6.0 | 6.25 | Connected least privilege, explicit deny, public-access prevention, versioning, encryption, and audit evidence |

**Why the increases were limited:** The workflow was guided, the exact reason a high-level `aws s3 cp` attempt returned `403 HeadObject Forbidden` while the direct `s3api get-object` call succeeded was not isolated, and independent reconstruction is still required. A future repeat should use `--debug` or equivalent evidence to explain such discrepancies instead of guessing.

---

### August 19, 2026 — Advanced IAM Boundaries, Trust Conditions, and Access Analyzer

**Evidence:** [AWS Security Lab: Permissions Boundaries, Trust Conditions, and Access Analyzer](aws-security/2026-08-19-advanced-iam-boundaries-trust-conditions-access-analyzer.md)

Demonstrated hands-on:

- Created a customer-managed permissions boundary containing three EC2 read actions.
- Created and assumed a test IAM role from an Identity Center administrator session.
- Proved that `AdministratorAccess` was capped by the boundary when IAM and S3 operations were denied.
- Isolated a Console dependency: direct `DescribeVpcs` succeeded while the VPC page failed because it also required `DescribeAccountAttributes`.
- Removed the role's permissions policy and proved that a boundary alone did not grant `DescribeVpcs`.
- Added a narrow inline identity policy and directly demonstrated the identity-policy/boundary intersection.
- Applied `aws:RequestedRegion` and proved the same `DescribeVpcs` action succeeded in `us-east-1` and failed in `us-west-1`.
- Added an `sts:ExternalId` trust condition and tested failed and successful new role assumptions without displaying credentials.
- Reconstructed allowed and denied EC2 and STS calls in CloudTrail, including role session, Region, external ID, error, and expiration.
- Located the target STS role under `requestParameters.roleArn` when the top-level resource list was empty.
- Used Access Analyzer policy validation to detect wildcard `iam:PassRole`, then removed the warning by restricting the role ARN and `iam:PassedToService`.
- Corrected the distinction between `iam:PassRole` and `sts:AssumeRole`.
- Deleted the role, boundary policy, inline policy, and local CLI profile.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Modern Identity | 5.0 | 5.25 | Direct trust-policy, ExternalId, STS session, PassRole, and AssumeRole evidence |
| AWS / Cloud Security | 6.0 | 6.25 | Practical permissions-boundary, policy-intersection, API-isolation, and Region-condition testing |
| Cloud / Modern Incident Response | 6.75 | 7.0 | Reconstructed successful and denied EC2/STS decisions from CloudTrail fields |
| Enterprise Security Controls | 6.25 | 6.5 | Demonstrated permission ceilings, conditional trust, least-privilege PassRole validation, and audit evidence |

**Why the increases were limited:** The lab was guided. The initial knowledge-check response omitted the boundary when explaining post-assumption authorization, and the initial `PassRole` answer also selected `AssumeRole`. Both were corrected during the lab. A larger increase should require independent policy reconstruction and troubleshooting in a new scenario.

---

## Evidence Rules for Future Daily Updates

After each new dated learning note:

1. Link the note in the daily history.
2. Record what was demonstrated, not merely discussed.
3. Increase only directly supported skill areas.
4. Keep the initial matrix unchanged.
5. Never raise a score solely because a guided lab was completed.
6. Prefer a small `+0.25` increase for new guided operational evidence.
7. Use `+0.5` only when several related skills were demonstrated or a workflow was repeated with reduced assistance.
8. Require independent reconstruction, troubleshooting, or transfer to a new scenario for larger gains.
9. Allow “no score change” on productive days when the work deepens knowledge without proving a new ability level.
10. Record regressions only when repeated evidence shows that a previously demonstrated capability is not retained.

---

## Current Strengths

- Detection and investigation reasoning
- Windows and endpoint-security foundations
- Malware/offensive mental models
- Correlating identity, control-plane, and network evidence
- Asking boundary and failure-path questions that expose design weaknesses

## Current Priority Gaps

1. Independently reconstruct AWS policy evaluation across trust, identity, resource, boundary, condition, and explicit-deny layers.
2. Cross-account IAM and service control policies in a safe multi-account or simulated design.
3. Workload identity and Kubernetes RBAC through hands-on labs.
4. Cloud-native incident reconstruction across CloudTrail, Flow Logs, GuardDuty, Config, workload logs, and identity-provider evidence.
5. End-to-end DevSecOps pipeline implementation and finding remediation.

---

## Next Evidence Opportunity

The next recommended note should document a **GuardDuty and cloud incident-investigation lab**:

- Enable or inspect GuardDuty with a clear cost check.
- Use AWS sample findings rather than generating malicious traffic.
- Interpret finding type, severity, actor, resource, and network context.
- Pivot from a finding into CloudTrail and any relevant network or workload telemetry.
- Build a concise incident timeline and containment decision.
- Remove temporary resources and review any continuing service state.

Successful completion would add practical evidence primarily for AWS / Cloud Security and Cloud / Modern Incident Response.
