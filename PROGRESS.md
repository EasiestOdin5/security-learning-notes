# Security Skills Progress Tracker

**Baseline date:** August 11, 2026  
**Last updated:** August 16, 2026  
**Scale:** 0–10, where 10 represents strong specialist-level working knowledge  
**Scoring policy:** Scores change only when dated notes contain demonstrated evidence. Discussion, recognition, or a correct guess alone does not increase a score.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Remaining gap |
|---|---:|---:|---:|---:|---:|
| Modern Identity | 4.0 | 4.5 | 8.0 | +0.5 | 3.5 |
| AWS / Cloud Security | 5.0 | 5.5 | 8.0 | +0.5 | 2.5 |
| Kubernetes Security | 5.0 | 5.0 | 8.0 | — | 3.0 |
| Cloud / Modern Incident Response | 6.0 | 6.25 | 8.0 | +0.25 | 1.75 |
| DevSecOps / CI-CD Security | 5.5 | 5.5 | 7.5 | — | 2.0 |
| Application Security | 6.0 | 6.0 | 7.5 | — | 1.5 |
| PKI / TLS / Secrets | 4.5 | 4.5 | 7.0 | — | 2.5 |
| Linux Security Operations | 6.0 | 6.0 | 7.0 | — | 1.0 |
| Vulnerability Management | 5.0 | 5.0 | 7.0 | — | 2.0 |
| Enterprise Security Controls | 5.5 | 5.75 | 7.0 | +0.25 | 1.25 |

### Overall interpretation

The strongest measured improvement so far is in **Modern Identity** and **AWS / Cloud Security**. The improvement is real but still guided: the labs were completed hands-on, while several traffic paths and authorization chains still required prompts to reconstruct.

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

1. Independently reconstruct AWS traffic and authorization paths without prompts.
2. EC2 IAM roles, instance profiles, IMDSv2, temporary credential rotation, and credential-theft implications.
3. Workload identity and Kubernetes RBAC through hands-on labs.
4. Cloud-native incident reconstruction across CloudTrail, Flow Logs, GuardDuty, workload logs, and identity-provider evidence.
5. End-to-end DevSecOps pipeline implementation and finding remediation.

---

## Next Evidence Opportunity

The next recommended note should document an **EC2 IAM role and IMDSv2 lab**:

- Create a least-privilege EC2 role and instance profile.
- Require IMDSv2.
- Retrieve metadata through an IMDSv2 token.
- Observe temporary role credentials without storing secrets.
- Perform one allowed and one denied API operation.
- Reconstruct both operations in CloudTrail.
- Explain credential use, expiration, refresh, and what happens after instance access is lost.

Successful completion with less prompting would support future increases in Modern Identity, AWS / Cloud Security, and Cloud / Modern Incident Response.
