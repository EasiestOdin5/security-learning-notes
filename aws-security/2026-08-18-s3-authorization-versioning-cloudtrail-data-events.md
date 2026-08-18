# AWS Security Lab: S3 Authorization, Versioning, and CloudTrail Data Events

**Session date:** August 18, 2026  
**Status:** Hands-on lab completed and temporary AWS/local resources cleaned up  
**Environment:** Amazon S3, IAM Identity Center, AWS CLI SSO, bucket policies, S3 Block Public Access, versioning, CloudTrail trails, and PowerShell

---

## 1. Lab Goals

The lab examined four related questions:

1. How can an identity be limited to one S3 prefix?
2. How do identity policies, bucket policies, implicit deny, and explicit deny combine?
3. How do Block Public Access and versioning protect S3 data?
4. Why does default CloudTrail Event History not show `GetObject`, and how can object reads be recorded?

The completed path was:

```text
Identity Center user
→ S3-scoped permission set
→ AWSReservedSSO assumed-role session
→ allowed and denied S3 API calls
→ bucket-level preventive controls
→ version recovery
→ CloudTrail S3 data-event evidence
```

---

## 2. Private Bucket and Object Prefixes

A private S3 bucket was created in `us-east-1` with a globally unique name following this pattern:

```text
security-lab-data-20260818-<random-suffix>
```

S3 Block Public Access remained fully enabled, and the remaining creation settings stayed at their defaults.

Two prefixes were created:

```text
allowed/
restricted/
```

The same harmless test object was uploaded under both prefixes:

```text
allowed/s3-lab-test.txt
restricted/s3-lab-test.txt
```

### Q: Are S3 folders traditional filesystem directories?

**A:** No. S3 is an object store. A name such as `allowed/s3-lab-test.txt` is an object key, and `allowed/` is a key prefix that the console presents like a folder.

### Q: Did merely creating the bucket or prefixes grant the scoped user access?

**A:** No. Authorization still depended on the user's assumed role, its identity policy, applicable bucket policy, Block Public Access, and other relevant controls.

---

## 3. Identity Center Permission Set

A custom IAM Identity Center permission set was created:

```text
S3LabScopedRead
```

It was assigned to the existing `lab-admin` Identity Center user for the AWS account. Identity Center provisioned a corresponding IAM role with a name similar to:

```text
AWSReservedSSO_S3LabScopedRead_<suffix>
```

The initial inline policy was:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListOnlyAllowedPrefix",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "allowed",
            "allowed/*"
          ]
        }
      }
    },
    {
      "Sid": "ReadAllowedObjects",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/allowed/*"
    }
  ]
}
```

### Q: Why does `s3:ListBucket` use the bucket ARN rather than an object ARN?

**A:** Listing operates on the bucket. The `s3:prefix` condition narrows which object-key prefixes the caller may request.

### Q: Why does `s3:GetObject` use `/allowed/*`?

**A:** Reading operates on objects, so the resource must identify the object-key namespace under the bucket.

### Important distinction

```text
Bucket-level action: s3:ListBucket  → arn:aws:s3:::BUCKET
Object-level action: s3:GetObject  → arn:aws:s3:::BUCKET/allowed/*
```

---

## 4. CLI SSO Session for the Scoped Role

A separate local CLI profile was configured:

```powershell
aws configure sso --profile s3-lab
```

Configuration included:

- Local SSO session name: `security-lab-sso`
- Existing Identity Center start URL
- Registration scope: `sso:account:access`
- Role/permission set: `S3LabScopedRead`
- Default Region: `us-east-1`
- Output format: `json`

The caller was verified with:

```powershell
aws sts get-caller-identity --profile s3-lab
```

The ARN contained:

```text
AWSReservedSSO_S3LabScopedRead
```

### Q: Did this create a permanent IAM-user access key?

**A:** No. The CLI used an Identity Center login and temporary role credentials.

### Q: What happened after the SSO token expired?

The CLI returned:

```text
Error when retrieving token from sso: Token has expired and refresh failed
```

The session was refreshed with:

```powershell
aws sso login --profile s3-lab
```

---

## 5. Testing the Identity Policy

### Allowed prefix listing

```powershell
aws s3 ls s3://YOUR_BUCKET_NAME/allowed/ --profile s3-lab
```

The command listed:

```text
s3-lab-test.txt
```

### Allowed direct object read

```powershell
aws s3api get-object `
  --bucket YOUR_BUCKET_NAME `
  --key allowed/s3-lab-test.txt `
  "$env:TEMP\s3-allowed-download.txt" `
  --profile s3-lab
```

The download succeeded, and `Get-Content` returned the expected test text.

### Denied prefix listing

```powershell
aws s3 ls s3://YOUR_BUCKET_NAME/restricted/ --profile s3-lab
```

The request returned `AccessDenied` because the `s3:prefix` condition did not match.

### Denied direct object read

```powershell
aws s3api get-object `
  --bucket YOUR_BUCKET_NAME `
  --key restricted/s3-lab-test.txt `
  "$env:TEMP\s3-restricted-download.txt" `
  --profile s3-lab
```

This also returned `AccessDenied` because no identity-based allow covered `restricted/*`.

### Q: Was the restricted-prefix result an explicit deny?

**A:** Not yet. It was an **implicit deny**: AWS denies a request when no applicable policy allows it.

### Unresolved observation: high-level `aws s3 cp`

The first high-level download attempt returned:

```text
403 Forbidden when calling HeadObject
```

The direct `s3api get-object` request then succeeded. This proved that `GetObject` authorization worked, but the precise cause of the preliminary `HeadObject` failure was not isolated during the lab. A future reproduction should use `--debug` and compare the exact bucket, key, request headers, and API sequence instead of assigning a cause without evidence.

---

## 6. Bucket Policy Explicit Deny

An S3 bucket policy was added:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ExplicitlyDenyReadingAllowedPrefix",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/allowed/*"
    }
  ]
}
```

The previously successful `GetObject` request then returned `AccessDenied`.

The `ListBucket` request for `allowed/` continued to work because the bucket-policy deny applied only to `s3:GetObject`.

### Final decision

```text
Identity policy: Allow s3:GetObject on allowed/*
Bucket policy:   Deny  s3:GetObject on allowed/*
Final result:    DENY
```

### Q: Did the bucket policy need to repeat the identity allow?

**A:** No. This same-account role already received an identity-based allow. The bucket policy was used here to add an overriding explicit deny.

### Q: Does an explicit deny remove unrelated permissions?

**A:** No. Policy statements are evaluated against the requested action, resource, principal, and conditions. The object-read deny did not deny bucket listing.

---

## 7. S3 Block Public Access

An attempt was made to replace the bucket policy with a public-read allow:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AttemptPublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/allowed/*"
    }
  ]
}
```

AWS rejected the policy because Block Public Access had remained enabled from bucket creation.

### Q: What does `Principal: "*"` mean in this allow statement?

**A:** It attempts to grant the stated action to any principal. For object reads, that would create public access unless another control prevented it.

### Q: Is Block Public Access merely a warning?

**A:** No. In this lab it acted as a preventive guardrail and rejected the public bucket-policy change.

After the test, the earlier explicit-deny policy was deleted. The scoped identity policy again allowed reading `allowed/*`.

---

## 8. Default Encryption

The bucket's default encryption was inspected and showed:

```text
SSE-S3
```

### Q: What does SSE-S3 mean?

**A:** S3 encrypts objects at rest using keys managed entirely by the S3 service. No customer-managed KMS key or KMS key policy was created in this lab.

### Q: Did this lab prove understanding of KMS key policies?

**A:** No. KMS and secrets remain a separate future lab. Inspecting SSE-S3 alone is not evidence of operating customer-managed KMS authorization.

---

## 9. Versioning and Recovery

S3 bucket versioning was enabled. The local test file was changed to:

```text
S3 authorization lab test - version 2
```

It was uploaded again with the same object key.

The console grouped two stored versions:

- Version ID `null`: object created before versioning was enabled
- Generated version ID: object uploaded after versioning was enabled

The current object returned version 2.

### Historical-version authorization

An attempt to retrieve the older `null` version returned `AccessDenied`:

```powershell
aws s3api get-object `
  --bucket YOUR_BUCKET_NAME `
  --key allowed/s3-lab-test.txt `
  --version-id null `
  "$env:TEMP\s3-old-version.txt" `
  --profile s3-lab
```

The permission set was updated from:

```json
"Action": "s3:GetObject"
```

to:

```json
"Action": [
  "s3:GetObject",
  "s3:GetObjectVersion"
]
```

The historical download then succeeded and returned the original content.

### Q: Why was `s3:GetObject` insufficient?

**A:** AWS defines reading the current object and reading a specific historical version as separately authorized actions.

### Delete-marker test

The current object was deleted while versioning was enabled. S3 created a latest **delete marker** rather than erasing the stored versions.

With versions displayed, the marker and both data versions remained visible. Deleting only the delete marker restored the newest underlying data version as the current visible object.

### Q: Does versioning prevent all data loss?

**A:** No. A principal with permission to permanently delete individual versions can still remove them. Versioning provides recovery from ordinary overwrites and delete-marker operations; permissions, MFA Delete where applicable, Object Lock, backups, and lifecycle controls address additional risks.

---

## 10. Management Events Versus Data Events

CloudTrail Event History was searched for the exact `GetObject` event, but it was absent.

### Q: Why was `GetObject` not in default Event History?

**A:** Default Event History focuses on management/control-plane events. S3 object operations such as `GetObject` are high-volume **data-plane events** and must be explicitly selected for logging.

Examples:

| Category | Example events | Meaning |
|---|---|---|
| Management event | `CreateBucket`, `PutBucketPolicy` | Configure or administer the service |
| Data event | `GetObject`, `PutObject`, `DeleteObject` | Operate on the data itself |

### Q: Why are S3 data events not enabled automatically for every bucket?

**A:** A busy application can generate enormous object-request volume. Explicit selection lets teams control scope, storage, and event charges.

---

## 11. Custom CloudTrail Trail

A temporary trail was created:

```text
security-lab-s3-data-trail
```

A separate S3 log bucket was created using this pattern:

```text
security-lab-cloudtrail-logs-20260818-<random-suffix>
```

The lab intentionally:

- Stored CloudTrail logs separately from the monitored data bucket
- Left log-file validation enabled
- Disabled optional CloudWatch delivery
- Did not create a customer-managed KMS key
- Selected data events rather than management events

### Advanced selector

The S3 object selector was narrowed to:

```text
eventCategory   = Data                 (supplied by S3 data-event type)
resources.type  = AWS::S3::Object     (supplied by S3 data-event type)
readOnly        = true
resources.ARN   starts with arn:aws:s3:::LAB_BUCKET/
eventName       = GetObject
```

### Q: Why use `StartsWith` for the bucket ARN?

**A:** S3 data-event resources are object ARNs. `StartsWith` on `arn:aws:s3:::BUCKET/` includes objects beneath that bucket while excluding other buckets.

### Q: Why store trail logs in a second bucket?

**A:** It separates protected data from audit evidence and avoids confusing monitored object activity with log-delivery objects. Production environments also protect central log storage with tighter access and retention controls.

---

## 12. Inspecting the Successful `GetObject` Event

After the trail began logging, a fresh allowed read was performed with the `s3-lab` profile.

CloudTrail delivered a compressed JSON log under a path similar to:

```text
AWSLogs/
→ ACCOUNT_ID/
→ CloudTrail/
→ us-east-1/
→ 2026/08/18/
→ <log-file>.json.gz
```

`CloudTrail-Digest` contained integrity-validation artifacts; the event records were under `CloudTrail`.

The downloaded JSON was parsed in PowerShell:

```powershell
$logFile = Get-ChildItem "$env:USERPROFILE\Downloads\*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

$log = Get-Content $logFile.FullName -Raw | ConvertFrom-Json

$log.Records | Select-Object `
    eventTime,
    eventName,
    @{Name="IdentityType";Expression={$_.userIdentity.type}},
    sourceIPAddress,
    @{Name="Bucket";Expression={$_.requestParameters.bucketName}},
    @{Name="ObjectKey";Expression={$_.requestParameters.key}}
```

The record showed:

```text
eventName: GetObject
bucket: the lab data bucket
object key: allowed/s3-lab-test.txt
identity type: AssumedRole
role: AWSReservedSSO_S3LabScopedRead_<suffix>
```

### Q: What did this prove?

**A:** It tied a specific object read to the scoped Identity Center assumed-role session, time, source IP, user agent, bucket, and object key.

---

## 13. Inspecting the Denied `GetObject` Event

A new request attempted to read:

```text
restricted/s3-lab-test.txt
```

The API returned `AccessDenied`. After CloudTrail delivered the next log file, PowerShell filtered for that object:

```powershell
$log.Records |
    Where-Object {
        $_.eventName -eq "GetObject" -and
        $_.requestParameters.key -eq "restricted/s3-lab-test.txt"
    } |
    Select-Object eventTime, eventName, errorCode, errorMessage
```

The record contained:

```text
eventName: GetObject
errorCode: AccessDenied
```

### Q: Why is logging denied access valuable?

**A:** A denied request can reveal reconnaissance, a broken application, a compromised identity testing its reach, or a policy that is narrower than the caller expected.

### Q: Is the API error alone enough for investigation?

**A:** No. Investigators should correlate the role/session, source IP, user agent, bucket/key, time, surrounding events, and expected workload behavior.

---

## 14. Review Questions and Answers

### Q1: What allowed listing only `allowed/`?

**A:** `s3:ListBucket` on the bucket ARN combined with a matching `s3:prefix` condition.

### Q2: What allowed reading the current object?

**A:** `s3:GetObject` on `arn:aws:s3:::BUCKET/allowed/*`.

### Q3: Why was `restricted/*` denied before a bucket policy existed?

**A:** No applicable allow existed, so the default decision was implicit deny.

### Q4: Why did the allowed object become denied after adding the bucket policy?

**A:** An applicable explicit deny overrides an identity-based allow.

### Q5: Why could the role still list `allowed/` during the object-read deny?

**A:** The deny targeted `s3:GetObject`, not `s3:ListBucket`.

### Q6: What prevented the public-read bucket policy?

**A:** S3 Block Public Access.

### Q7: What was the bucket's default encryption?

**A:** SSE-S3.

### Q8: Why did the old version require another permission?

**A:** Historical reads require `s3:GetObjectVersion`.

### Q9: What did an ordinary delete do after versioning was enabled?

**A:** It added a delete marker while retaining the stored object versions.

### Q10: How was the object restored?

**A:** The latest delete marker was permanently deleted, exposing the newest stored data version again.

### Q11: Why was `GetObject` absent from default Event History?

**A:** It is an S3 data event, not a default management event.

### Q12: What did the custom trail add?

**A:** Narrow logging of `GetObject` data events for objects in the one lab bucket.

### Q13: Did CloudTrail capture denied reads?

**A:** Yes. The denied request appeared with `errorCode: AccessDenied`.

### Q14: What identified the human-backed role session?

**A:** `userIdentity.type: AssumedRole` and an ARN containing `AWSReservedSSO_S3LabScopedRead`.

---

## 15. Corrections and Strengthened Mental Models

### Correction 1: S3 folders

**Incorrect:** `allowed` and `restricted` are ordinary directories.  
**Correct:** They are object-key prefixes.

### Correction 2: Deny type

**Incorrect:** Every failed request has an explicit deny.  
**Correct:** `restricted/*` initially failed because of implicit deny; the bucket-policy test added a separate explicit deny.

### Correction 3: Policy scope

**Incorrect:** An object-read deny automatically prevents bucket listing.  
**Correct:** AWS evaluates the exact action and resource; `GetObject` and `ListBucket` are separate.

### Correction 4: Block Public Access

**Incorrect:** It is only a console warning about public policies.  
**Correct:** It prevented the public-allow bucket policy from being accepted.

### Correction 5: Version deletion

**Incorrect:** Deleting the current object immediately erased every stored version.  
**Correct:** Versioning created a delete marker, and removing that marker restored visibility.

### Correction 6: CloudTrail depth

**Incorrect:** If an AWS API call is not in default Event History, CloudTrail cannot record it.  
**Correct:** CloudTrail can record selected data events, but they must be explicitly configured.

### Correction 7: Audit identity

**Incorrect:** The event would identify the caller simply as `lab-admin`.  
**Correct:** AWS recorded an assumed-role ARN generated from the `S3LabScopedRead` Identity Center permission set.

---

## 16. Cleanup Performed

The following temporary resources were removed:

- CloudTrail trail `security-lab-s3-data-trail`
- Separate CloudTrail log bucket and its log/digest objects
- Original S3 lab bucket, both prefixes, all object versions, and delete markers
- Identity Center account assignment for `S3LabScopedRead`
- Identity Center permission set `S3LabScopedRead`
- Local temporary object-download files
- Downloaded CloudTrail JSON/JSON.GZ files

The local AWS CLI profile named `s3-lab` may remain as an inert configuration reference. It has no charge and can no longer obtain that deleted assignment.

---

## 17. Demonstrated Progress

Hands-on evidence included:

- Creating a private S3 bucket with Block Public Access enabled.
- Distinguishing S3 prefixes from directories.
- Building a prefix-scoped Identity Center permissions policy.
- Creating and verifying a separate CLI SSO profile.
- Testing successful and denied bucket/object operations.
- Distinguishing implicit deny from explicit deny.
- Proving a bucket-policy explicit deny overrides an identity allow.
- Proving an action-specific deny did not remove unrelated listing access.
- Observing Block Public Access reject a public bucket policy.
- Inspecting SSE-S3 encryption without overstating KMS knowledge.
- Enabling versioning, observing a `null` version, and adding `GetObjectVersion`.
- Creating and removing a delete marker to recover an object.
- Distinguishing CloudTrail management events from S3 data events.
- Creating a narrowly filtered CloudTrail trail for `GetObject`.
- Parsing successful and denied S3 object-access events from JSON.
- Attributing the event to the scoped Identity Center assumed role.
- Cleaning up AWS and local artifacts.

The work was still guided, but it demonstrated an end-to-end preventive-and-detective control chain. Future scoring should require independent reconstruction or application to a new S3 scenario before another increase in these same areas.

---

## 18. Recommended Next Lab

The next lab should cover **advanced IAM policy evaluation**:

1. Compare identity and resource policies across two roles.
2. Add policy conditions such as source VPC endpoint, Region, or principal ARN.
3. Introduce a permissions boundary.
4. Demonstrate that a boundary limits maximum identity permissions but does not grant access.
5. Use IAM Policy Simulator or Access Analyzer where appropriate.
6. Test allowed and denied calls.
7. Reconstruct the decisions in CloudTrail.
8. Clean up all temporary identities and policies.
