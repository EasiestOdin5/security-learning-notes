# AWS Security Lab: Permissions Boundaries, Trust Conditions, and Access Analyzer

**Session date:** August 19, 2026  
**Status:** Hands-on lab completed; AWS and local lab artifacts cleaned up  
**Environment:** IAM, IAM Identity Center, STS, AWS CLI SSO, EC2 read APIs, CloudTrail Event History, and IAM Access Analyzer policy validation

---

## 1. Lab Goals

This lab tested five related IAM questions:

1. Does a permissions boundary grant permissions?
2. How are identity-policy permissions combined with a boundary?
3. How can a condition restrict an otherwise allowed API request?
4. How does a role trust policy differ from the role's permissions?
5. How can CloudTrail and Access Analyzer explain or prevent unsafe authorization?

The practical path was:

```text
Identity Center administrator session
→ assume test IAM role
→ identity policy and permissions boundary evaluation
→ Region condition evaluation
→ trust-policy ExternalId evaluation
→ CloudTrail success/denial evidence
→ Access Analyzer static policy validation
```

---

## 2. Resources Created

- Customer-managed boundary policy: `SecurityLabEC2ReadBoundary`
- IAM role: `security-lab-boundary-role`
- Inline role policy: `SecurityLabRequestedPermissions`
- Local AWS CLI role profile: `boundary-lab`

All were deleted or removed at the end of the lab.

---

## 3. Permissions Boundary

The boundary allowed only three EC2 read actions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets"
      ],
      "Resource": "*"
    }
  ]
}
```

The test role initially had:

- `AdministratorAccess` as its permissions policy.
- `SecurityLabEC2ReadBoundary` as its permissions boundary.
- The local AWS account as its trusted entity.

The role was assumed from the Identity Center administrator session. Opening IAM produced an error for `iam:ListRoles` with the explanation that no permissions boundary allowed the action. Listing S3 buckets was also denied.

### Core rule

A permissions boundary is a **maximum-permissions ceiling**. It does not independently grant access.

```text
Identity policy allows action
AND
Boundary allows action
→ action may be allowed
```

If either side does not allow the action, the role does not receive that permission.

---

## 4. Why the VPC Console Failed but the API Worked

The VPC Console page produced an authorization error for:

```text
ec2:DescribeAccountAttributes
```

The boundary allowed `ec2:DescribeVpcs` but did not allow `ec2:DescribeAccountAttributes`. This showed that one Console page can call several APIs.

The exact API was isolated with the CLI:

```powershell
aws ec2 describe-vpcs --profile boundary-lab --region us-east-1 --query "Vpcs[].VpcId"
```

That command succeeded.

The following command failed with `UnauthorizedOperation`:

```powershell
aws ec2 describe-account-attributes --profile boundary-lab --region us-east-1
```

### Lesson

A failed Console page does not prove that the most obvious API was denied. Identify the specific failed API from the error or CloudTrail, then test that API directly.

---

## 5. Proving That a Boundary Grants Nothing

`AdministratorAccess` was removed from the test role while the boundary remained attached.

The role then had:

```text
Identity policy: no grant for DescribeVpcs
Boundary: allows DescribeVpcs
Result: denied
```

The direct `describe-vpcs` command returned `UnauthorizedOperation`. This proved that the boundary alone did not grant the action.

---

## 6. Testing the Policy Intersection

The role received this inline identity policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RequestedPermissions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "s3:ListAllMyBuckets"
      ],
      "Resource": "*"
    }
  ]
}
```

Results:

| Action | Identity policy | Boundary | Effective result |
|---|---|---|---|
| `ec2:DescribeVpcs` | Allow | Allow | Allowed |
| `s3:ListAllMyBuckets` | Allow | Not included | Denied |

The result directly demonstrated the intersection between the two policy layers.

---

## 7. Region Condition

The identity policy was updated so `DescribeVpcs` was allowed only in `us-east-1`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DescribeVpcsOnlyInUsEast1",
      "Effect": "Allow",
      "Action": "ec2:DescribeVpcs",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "RequestS3List",
      "Effect": "Allow",
      "Action": "s3:ListAllMyBuckets",
      "Resource": "*"
    }
  ]
}
```

Tests:

```powershell
aws ec2 describe-vpcs --profile boundary-lab --region us-east-1 --query "Vpcs[].VpcId"
```

Result: success.

```powershell
aws ec2 describe-vpcs --profile boundary-lab --region us-west-1 --query "Vpcs[].VpcId"
```

Result: `UnauthorizedOperation`.

The same identity and API action produced different results because `aws:RequestedRegion` matched in one request and not the other.

---

## 8. Trust Policy and External ID

The previous policies controlled what the role could do **after** assumption. The role trust policy controlled whether a new role session could be created.

The current role assumption was first verified without displaying credentials:

```powershell
aws sts assume-role `
  --role-arn $RoleArn `
  --role-session-name trust-test `
  --profile AdministratorAccess-ACCOUNT_ID `
  --query "Credentials.Expiration" `
  --output text
```

The trust policy was then updated to require:

```json
"Condition": {
  "StringEquals": {
    "sts:ExternalId": "SecurityLabExternalId"
  }
}
```

Results:

| AssumeRole request | Trust condition | Result |
|---|---|---|
| No external ID | False | `AccessDenied` |
| Correct external ID | True | New temporary session created |

### What an external ID is

An external ID is a request value used primarily in third-party, cross-account role assumption to prevent the **confused deputy problem**. It binds a request to the intended customer relationship.

It is not a password:

- The caller must already be an authenticated AWS principal.
- The caller still needs permission to call `sts:AssumeRole`.
- The role must trust the caller.
- The condition must match.
- CloudTrail can record the external ID in request parameters.

---

## 9. CloudTrail Reconstruction

CloudTrail Event History showed successful and denied `DescribeVpcs` events.

The denied event contained:

- `userIdentity.arn` for `security-lab-boundary-role/lab-admin`
- `awsRegion` of `us-west-1`
- An authorization error

The successful event contained:

- The same assumed-role identity
- `awsRegion` of `us-east-1`
- No `errorCode`

CloudTrail also showed `AssumeRole` events:

- `trust-test-no-id` returned `AccessDenied`.
- `trust-test-with-id` contained the expected external ID and credential expiration.

For STS events, the top-level Resources section could be empty. The target role was still visible in:

```text
requestParameters.roleArn
```

This corrected the possible misunderstanding that an empty Resources field meant no role had been targeted.

---

## 10. Access Analyzer Policy Validation

An intentionally risky policy was entered into the IAM policy editor but never created:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    }
  ]
}
```

Access Analyzer warned that wildcard `iam:PassRole` access could be overly permissive.

The policy was narrowed to one role and one receiving service:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PassOnlyBoundaryRoleToEC2",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::ACCOUNT_ID:role/security-lab-boundary-role",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ec2.amazonaws.com"
        }
      }
    }
  ]
}
```

The warning disappeared.

### Important limitation

No validation warning means the policy passed AWS's static checks. It does not prove that the policy is appropriate, sufficient, or secure for the environment.

---

## 11. `PassRole` Versus `AssumeRole`

These actions solve different problems:

```text
Administrator --iam:PassRole--> assigns role to EC2
EC2 service --sts:AssumeRole--> obtains a session for that role
```

- `iam:PassRole` permits a caller to give a role to an AWS service.
- `sts:AssumeRole` permits creation of a role session.
- Assigning a role while launching EC2 also requires the relevant EC2 operation, such as `ec2:RunInstances`.

The initial answer to the knowledge check selected both `PassRole` and `AssumeRole`. The correction was that the administrator needs `iam:PassRole` to assign the role; EC2 performs the role assumption.

---

## 12. Questions and Answers

### Q1. Does a permissions boundary grant access?

**Answer:** No. It defines the maximum permissions that an identity policy can grant.

### Q2. Why was S3 denied even though the inline identity policy allowed it?

**Answer:** The boundary did not include S3, so S3 was outside the role's maximum permissions.

### Q3. Why did `DescribeVpcs` fail after the permissions policy was removed?

**Answer:** The boundary still allowed the action, but there was no identity-policy grant. A boundary alone grants nothing.

### Q4. Why did the VPC Console fail even though direct `DescribeVpcs` succeeded?

**Answer:** The Console also called `DescribeAccountAttributes`, which the boundary did not allow.

### Q5. Why did the same `DescribeVpcs` command work in one Region and fail in another?

**Answer:** The identity policy's `aws:RequestedRegion` condition allowed only `us-east-1`.

### Q6. What controls whether a role session can be created?

**Answer:** The caller's permission to request assumption plus the target role's trust policy and any trust conditions.

### Q7. After a role is assumed, what controls `DescribeVpcs`?

**Answer:** The identity policy and permissions boundary. The initial response named only the identity policy; the boundary must also allow the action.

### Q8. Is an external ID a password?

**Answer:** No. It is a role-assumption request value used mainly to prevent third-party customer/role confusion. Authentication and trust are still required.

### Q9. Why could an STS event have no top-level resource type?

**Answer:** STS events may record the targeted role under `requestParameters.roleArn` rather than the top-level Resources list.

### Q10. What is the difference between `iam:PassRole` and `sts:AssumeRole`?

**Answer:** `PassRole` authorizes assigning a role to a service. `AssumeRole` creates a temporary session as a role.

### Q11. Does an Access Analyzer result with no warning prove a policy is secure?

**Answer:** No. It is static validation, not a complete business-context or architecture review.

---

## 13. Compact Authorization Model

For this lab, the decision can be reconstructed as:

```text
Can a session be created?
→ caller permission + role trust policy + trust conditions

Can the session call the API?
→ identity-policy allow
→ permissions-boundary allow
→ request conditions match
→ no applicable explicit deny
```

This is a stronger model than treating a role as one undifferentiated set of permissions.

---

## 14. Cleanup

Completed cleanup:

- Deleted `security-lab-boundary-role`.
- Deleted the role's inline policy with the role.
- Deleted `SecurityLabEC2ReadBoundary`.
- Removed the local `[profile boundary-lab]` CLI configuration block.
- Did not create the sample `iam:PassRole` policy.

IAM roles, policies, CloudTrail Event History, and these tests did not leave a billable compute or storage resource.

---

## 15. Demonstrated Progress

This lab provided evidence for:

- Separating role trust from effective permissions.
- Proving that a permissions boundary limits but does not grant.
- Isolating hidden Console dependencies with exact CLI API tests.
- Applying and testing a global Region condition.
- Testing successful and denied role assumption with an external ID.
- Reconstructing authorization from raw CloudTrail fields.
- Interpreting empty STS resource lists correctly.
- Using Access Analyzer to improve a risky `PassRole` policy.
- Distinguishing `PassRole` from `AssumeRole` after correction.
- Cleaning up IAM and local CLI artifacts.

The work was guided. Before a larger score increase, the complete trust-and-permissions decision should be reconstructed independently in a new scenario.

---

## 16. Recommended Next Lab

The next lab should cover **GuardDuty and cloud incident investigation**:

1. Enable or inspect GuardDuty safely.
2. Generate or use sample findings instead of creating real malicious traffic.
3. Interpret finding type, resource, actor, network details, and severity.
4. Pivot from the finding into CloudTrail and other available telemetry.
5. Build a short incident timeline and containment decision.
6. Clean up any temporary resources and review ongoing cost.
