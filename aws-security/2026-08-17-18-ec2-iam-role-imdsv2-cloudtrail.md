# AWS Security Lab: EC2 IAM Role, IMDSv2, Least Privilege, and CloudTrail

**Session dates:** August 17–18, 2026  
**Status:** Hands-on lab completed and temporary resources cleaned up  
**Environment:** AWS IAM, EC2 Amazon Linux 2023, IAM Identity Center, EC2 Instance Connect, IMDSv2, AWS CLI, S3 API, EC2 API, and CloudTrail

---

## 1. Lab Goal

The core problem was:

> An application running on EC2 needs to call AWS services, but a permanent access key should not be stored on the server.

The lab implemented this pattern:

```text
EC2 workload
→ attached IAM role
→ temporary credentials delivered through IMDSv2
→ AWS API request
→ permissions-policy decision
→ CloudTrail evidence
```

The goals were to:

1. Separate a role's trust policy from its permissions policy.
2. Give EC2 a workload identity without storing a permanent access key.
3. Permit one AWS API action and deny an unrelated one.
4. require an IMDSv2 token for metadata access.
5. Trace allowed and denied role activity in CloudTrail.
6. Understand what malware could do with the instance role.
7. Understand expiration, refresh, and external use of stolen temporary credentials.

---

## 2. Identity Center Roles Versus an EC2 Role

### Q: Is `AdministratorAccess` a role?

**A:** No. `AdministratorAccess` is an AWS-managed permissions policy.

For the human login used in this lab, the chain was:

```text
Identity Center user: lab-admin
→ account assignment
→ permission set containing AdministratorAccess
→ provisioned AWSReservedSSO IAM role
→ temporary assumed-role session
```

For the EC2 workload, the chain was different:

```text
EC2 service
→ assumes security-lab-ec2-imds-role
→ temporary role session for the instance
→ application or command uses that identity
```

### Q: Is an EC2 role similar to a machine account in Active Directory?

**A:** As a mental model, yes. Both provide a non-human workload identity. An EC2 role is specifically an IAM role whose temporary credentials can be made available to software running on an instance.

### Q: Is the permission assigned separately to each application?

**A:** Usually not when one IAM role is attached to one EC2 instance. The role is attached at the instance/workload boundary. Any process on the instance that can reach IMDS and use the credentials can potentially exercise the role's permissions.

This is why one instance should not host unrelated applications that require very different privileges unless stronger isolation is added.

---

## 3. Trust Policy and Permissions Policy

The role created for the lab was:

```text
security-lab-ec2-imds-role
```

### Q: What did the trust policy do?

The role trusted the EC2 service principal:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "ec2.amazonaws.com"
  },
  "Action": "sts:AssumeRole"
}
```

This answered:

> Who is allowed to obtain a session for this role?

### Q: Is `ec2.amazonaws.com` like the user?

**A:** It is the trusted **service principal**. It identifies the AWS EC2 service in the trust decision.

### Q: Is `sts:AssumeRole` the same as an S3 or EC2 permission?

**A:** No. `sts:AssumeRole` permits the trusted principal to obtain or "wear" the role identity. It does not by itself grant access to S3, EC2, or other services.

### Q: What did the permissions policy do?

An inline identity-based policy allowed only:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowListingS3Buckets",
      "Effect": "Allow",
      "Action": "s3:ListAllMyBuckets",
      "Resource": "*"
    }
  ]
}
```

This answered:

> After the role session exists, what may that session do?

### Core model

```text
Trust policy       = who may obtain the role session
Permissions policy = what that role session may do
```

Both are authorization gates. Passing the trust gate does not imply broad AWS access.

---

## 4. EC2 Configuration

The instance was launched with:

- Name: `security-lab-ec2-imds`
- AMI: Amazon Linux 2023
- Instance type: `t3.micro`
- Region: `us-east-1`
- VPC: `security-lab-vpc`
- Subnet: `security-lab-public-a`
- Public IPv4: enabled
- Key pair: none
- Connection: browser-based EC2 Instance Connect
- IAM instance profile: `security-lab-ec2-imds-role`
- Metadata version: V2 only, token required

### Q: Why was the public subnet selected?

**A:** This lab used browser-based EC2 Instance Connect over the instance's public IPv4. A private-subnet design would require a different route, an EC2 Instance Connect Endpoint, Session Manager, VPN, or another management path.

### Q: Why was no SSH key pair created?

**A:** EC2 Instance Connect generated and delivered a short-lived SSH public key for the browser connection. A permanent local `.pem` file was not needed.

### Q: What source was intended for inbound SSH?

The Security Group allowed TCP 22 only from the AWS-managed regional prefix list:

```text
com.amazonaws.us-east-1.ec2-instance-connect
```

The actual Security Group rule stores a prefix-list ID beginning with `pl-`; typing the name as a CIDR string caused a malformed-CIDR launch error.

### Important region correction

The console was in `us-east-1`, not `us-west-1`. AWS-managed prefix lists are regional, so the correct prefix list had to match the instance's Region.

---

## 5. Troubleshooting the Failed Browser Connection

### Symptom

EC2 Instance Connect returned:

```text
Failed to connect to your instance
Error establishing SSH connection to your instance
```

### Investigation

The instance had:

- A public IPv4 address.
- A running state with all status checks passing.
- The intended public subnet.

However, its attached Security Group was the VPC's `default` group. Its inbound rule allowed traffic only from resources sharing that same Security Group. It did not allow TCP 22 from the EC2 Instance Connect prefix list.

### Fix

The instance's primary network interface was opened:

```text
EC2 instance
→ Networking tab
→ eni-... network interface
→ Actions
→ Change security groups
```

`security-lab-imds-sg` was attached and `default` was removed. Browser-based EC2 Instance Connect then succeeded.

### Q: Why were there two default Security Groups?

**A:** Every VPC has its own default Security Group. The account contained both the AWS default VPC and the separate `security-lab-vpc`, so two default groups were normal.

### Troubleshooting lesson

Do not assume that a Security Group created during an attempted launch was attached to the final instance. Verify the instance's ENI and its associated Security Group directly.

---

## 6. Verifying the EC2 Workload Identity

Inside the browser terminal, the identity was checked with:

```bash
aws sts get-caller-identity
```

The ARN followed this pattern:

```text
arn:aws:sts::ACCOUNT_ID:assumed-role/security-lab-ec2-imds-role/i-INSTANCE_ID
```

### Q: What did the ARN show?

- `assumed-role` — temporary STS role session.
- `security-lab-ec2-imds-role` — the IAM role being used.
- `i-INSTANCE_ID` — the session name identifying the EC2 instance.

This showed that commands running on the instance were not using the human `lab-admin` session.

---

## 7. Allowed and Denied API Tests

### Allowed action

```bash
aws s3api list-buckets --query 'Buckets[].Name'
```

The result was:

```json
[]
```

### Q: Did an empty list mean the request failed?

**A:** No. It meant the request succeeded but the account had no S3 buckets to return.

### Denied action

```bash
aws ec2 describe-instances --region us-east-1
```

The result was `UnauthorizedOperation`. The message explained that no identity-based policy allowed:

```text
ec2:DescribeInstances
```

### Q: What did these two tests prove?

The same assumed-role session received different decisions based on the requested action:

```text
s3:ListAllMyBuckets → allowed
ec2:DescribeInstances → denied
```

This was a direct least-privilege demonstration.

---

## 8. IMDSv2 Token and Role Metadata

The EC2 Instance Metadata Service is available from the instance at the link-local address:

```text
169.254.169.254
```

### Request an IMDSv2 token

```bash
TOKEN=$(curl -sS -X PUT \
  http://169.254.169.254/latest/api/token \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
```

The token was verified without displaying it:

```bash
echo ${#TOKEN}
```

The observed length was `56` characters.

### Q: Is the IMDSv2 token an AWS credential?

**A:** No. It authorizes requests to that instance's metadata service for the requested lifetime. It is then placed in the `X-aws-ec2-metadata-token` header.

### Retrieve the attached role name

```bash
curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

The response was:

```text
security-lab-ec2-imds-role
```

### Inspect only non-secret credential metadata

```bash
curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/security-lab-ec2-imds-role \
  | grep -E '"Code"|"Type"|"LastUpdated"|"Expiration"'
```

The full response was intentionally not displayed or stored because it also contains:

- Temporary access key ID
- Temporary secret access key
- Session token
- Expiration

### Q: What happens when the temporary credentials approach expiration?

**A:** While the role remains attached and the workload can reach IMDS, AWS provides replacement credentials. Applications using a current AWS SDK or AWS CLI credential provider normally retrieve and refresh them automatically.

---

## 9. Proving IMDSv2 Was Required

An IMDS request was sent without a token:

```bash
curl -i --max-time 5 \
  http://169.254.169.254/latest/meta-data/
```

The response was:

```text
HTTP/1.1 401 Unauthorized
```

### Q: What did this prove?

**A:** Tokenless IMDSv1-style requests were rejected. Requests containing the valid IMDSv2 token succeeded.

### Q: Would IMDSv2 stop malware already executing locally?

**A:** Usually not by itself. Local code can normally perform the token request and then query metadata. IMDSv2 is especially valuable against many SSRF and misconfigured-proxy paths because an attacker must perform the token-request step and supply the token header.

IMDSv2 is one layer, not a substitute for patching, workload isolation, endpoint controls, and least-privilege IAM.

---

## 10. CloudTrail Reconstruction

CloudTrail Event History contained the successful S3 request:

```text
eventName: ListBuckets
userIdentity.type: AssumedRole
role: security-lab-ec2-imds-role
sourceIPAddress: EC2 public IPv4
ec2RoleDelivery: 2.0
```

CloudTrail also contained the denied EC2 request:

```text
eventName: DescribeInstances
errorCode: Client.UnauthorizedOperation
userIdentity.type: AssumedRole
role: security-lab-ec2-imds-role
sourceIPAddress: EC2 public IPv4
ec2RoleDelivery: 2.0
```

### Q: Why were there many `DescribeInstances` events?

**A:** The AWS Console frequently calls `DescribeInstances` to populate EC2 pages. The lab event was isolated using the approximate event time, role name, source IP, and authorization error.

### Q: How could the request be attributed to the EC2 workload?

The evidence was combined:

1. The ARN named `security-lab-ec2-imds-role`.
2. The ARN's session name contained the instance ID.
3. `sourceIPAddress` matched the instance's public IPv4.
4. `ec2RoleDelivery: 2.0` showed that the credentials had been delivered using IMDSv2.
5. The event time and action matched the command that was run.

### Important correction

The assumed-role ARN alone does not prove that the API request physically came from the EC2 instance. Stolen temporary credentials preserve the same role identity. Source IP and surrounding evidence are required for stronger attribution.

---

## 11. Credential Theft and Malware Questions

### Q: If malware runs as `ec2-user`, can it call `ListBuckets`?

**A:** Yes, if it can reach IMDS and obtain or use the role credentials. It inherits the workload's AWS authorization boundary.

### Q: Could it call `DescribeInstances`?

**A:** No, not with this role, because the permissions policy did not allow `ec2:DescribeInstances`.

### Q: Does IMDSv2 stop local malware from obtaining role credentials?

**A:** Not normally. Malware already executing on the host can usually request its own IMDSv2 token. The main damage limiter demonstrated here was the role's least-privilege policy.

### Q: Can stolen EC2 temporary credentials be used outside the original instance?

**A:** Yes. The access key ID, secret access key, and session token are portable and can normally be used from another system until expiration.

### Q: What would CloudTrail show if they were used externally?

The event would still show the EC2 assumed-role identity and may show `ec2RoleDelivery: 2.0`, but `sourceIPAddress` could be an unfamiliar external address rather than the expected workload egress address.

### Q: Can an attacker refresh them after losing all access to the instance?

**A:** No, not merely from the expired credential set. The attacker would need renewed access to IMDS or another authorized way to obtain replacement credentials. Once the stolen credentials expire, they stop working.

---

## 12. Review Questions and Answers

### Q1: What gives EC2 permission to obtain the role session?

**A:** The role trust policy naming the EC2 service principal and allowing `sts:AssumeRole`.

### Q2: What gives the resulting session permission to list S3 buckets?

**A:** The role's identity-based permissions policy allowing `s3:ListAllMyBuckets`.

### Q3: Does `sts:AssumeRole` allow access to S3?

**A:** No. It allows the trusted principal to obtain the role session. Service permissions are evaluated separately.

### Q4: Why did `ListBuckets` return `[]` rather than `AccessDenied`?

**A:** Authorization succeeded, but there were no buckets.

### Q5: Why did `DescribeInstances` fail?

**A:** No identity-based policy attached to the role allowed `ec2:DescribeInstances`.

### Q6: What does `401 Unauthorized` from the tokenless metadata request mean?

**A:** The instance required IMDSv2 tokens, so IMDSv1-style access was blocked.

### Q7: What does `ec2RoleDelivery: 2.0` mean in CloudTrail?

**A:** The credentials used for the request were delivered using IMDSv2.

### Q8: Does a matching EC2 role ARN prove the network origin?

**A:** No. Correlate the role session, instance ID, source IP, event time, user agent, action, and other context.

### Q9: What happens to stolen temporary credentials at expiration?

**A:** They stop working. They do not refresh themselves outside the mechanism that originally supplied them.

### Q10: Which control limited the malware scenario most directly in this lab?

**A:** Least-privilege IAM. The workload could list buckets but could not enumerate EC2 instances.

---

## 13. Corrections to Preserve

### Correction 1: Role versus policy

**Incorrect:** `AdministratorAccess` is the role.  
**Correct:** `AdministratorAccess` is a permissions policy. Identity Center provisions an IAM role that contains or references the policy.

### Correction 2: Trust versus service permission

**Incorrect:** `sts:AssumeRole` means EC2 can perform AWS service actions.  
**Correct:** It permits obtaining the role session; the permissions policy separately controls service actions.

### Correction 3: Running on EC2

**Incorrect:** Any code can use AWS permissions merely because it runs on EC2.  
**Correct:** It needs access to usable credentials, commonly through IMDS and the attached role.

### Correction 4: IMDSv2 scope

**Incorrect:** IMDSv2 prevents local malware from obtaining credentials.  
**Correct:** It mainly raises the barrier for SSRF and proxy-based metadata abuse; local code can usually perform the token flow.

### Correction 5: Credential portability

**Incorrect:** EC2 role credentials work only from the original instance.  
**Correct:** The credential set is normally usable elsewhere until expiration unless an additional policy condition restricts its use.

### Correction 6: CloudTrail attribution

**Incorrect:** An assumed-role ARN alone proves that the request originated on EC2.  
**Correct:** The identity shows which credentials were used; network origin requires correlation with source IP and other context.

---

## 14. Cleanup Performed

The following temporary resources were removed:

- EC2 instance `security-lab-ec2-imds`
- Security Group `security-lab-imds-sg`
- IAM role `security-lab-ec2-imds-role`
- Inline S3 permission attached to that role

The retained VPC, subnets, route tables, Internet Gateway, and default Security Groups remain available for future labs.

---

## 15. Demonstrated Progress

This lab moved EC2 workload identity and metadata credentials from prompted discussion into direct observation.

Hands-on evidence included:

- Creating an EC2-trusted IAM role.
- Separating trust and permission policies.
- Adding a tightly scoped S3 permission.
- Attaching the role through an EC2 instance profile.
- Restricting browser SSH to the EC2 Instance Connect managed prefix list.
- Correcting a Region-specific prefix-list mistake.
- Diagnosing a failed connection caused by the wrong attached Security Group.
- Verifying the assumed-role identity from inside the EC2 instance.
- Performing one allowed and one denied AWS API action.
- Requesting and using an IMDSv2 token.
- Proving tokenless metadata access returned `401 Unauthorized`.
- Observing temporary credential expiration without exposing secrets.
- Reconstructing the allowed and denied role activity in CloudTrail.
- Correlating role, instance session, source IP, API action, error, and `ec2RoleDelivery`.
- Correcting the model that stolen temporary credentials are bound to the original instance.
- Cleaning up temporary resources.

The remaining weakness is independent reconstruction. The lab was successfully completed, including troubleshooting, but several IAM and credential-portability conclusions still required questions and correction before they were stated independently.

---

## 16. Recommended Next Lab

The next lab should cover **S3 authorization and data protection**:

1. Create a private test bucket.
2. Compare an IAM identity policy with a bucket resource policy.
3. Add a scoped allow for one prefix.
4. Add and observe an explicit deny.
5. Confirm Block Public Access behavior.
6. Test allowed and denied object operations.
7. Reconstruct the activity in CloudTrail, including the difference between management and data events.
8. Clean up the bucket and test objects.
