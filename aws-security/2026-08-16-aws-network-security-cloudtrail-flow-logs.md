# AWS Security Lab: Explicit Deny, EC2 Networking, CloudTrail, and VPC Flow Logs

**Session date:** August 16, 2026  
**Status:** Hands-on lab completed and temporary resources cleaned up  
**Environment:** AWS Console, IAM Identity Center, EC2 Amazon Linux 2023, VPC, Security Groups, Network ACLs, CloudTrail, VPC Flow Logs, CloudWatch Logs, and Windows PowerShell/OpenSSH

---

## 1. Starting Point and Lab Objectives

This session continued after the prior AWS SSO, CLI, IAM, and CloudTrail check-in.

The goals were to:

1. Demonstrate how an explicit deny overrides broad administrative access.
2. Trace inbound and return SSH traffic through an AWS VPC.
3. Test Security Group statefulness and NACL statelessness directly.
4. Reconstruct AWS configuration changes from CloudTrail.
5. Observe accepted and rejected network traffic with VPC Flow Logs.
6. Clean up temporary and potentially billable resources.

---

## 2. Permission Sets, Policies, and Explicit Deny

### Q: Is `AdministratorAccess` a role?

**A:** `AdministratorAccess` is an AWS-managed **permission policy**, not an identity by itself.

In IAM Identity Center, a permission set can include that managed policy. AWS then provisions an IAM role with a name similar to:

```text
AWSReservedSSO_AdministratorAccess_<suffix>
```

When the user selects that assignment in the AWS access portal, the user assumes the generated role and receives temporary credentials.

### Q: Did the `lab-admin` user itself have a role?

**A:** `lab-admin` was the Identity Center username. It received access through AWS-account assignments and permission sets.

The effective chain was:

```text
lab-admin
→ AWS account assignment
→ permission set
→ AWSReservedSSO role
→ temporary STS assumed-role session
```

### Q: What does “policy” mean?

**A:** A policy is a JSON authorization document containing statements that describe allowed or denied AWS API actions and the resources to which they apply.

Important statement fields include:

- `Effect`: `Allow` or `Deny`
- `Action`: the AWS API operations affected
- `Resource`: the resources affected
- `Condition`: optional restrictions

### Q: How was `AdminExceptTagging` constructed?

The permission set combined:

1. The AWS-managed `AdministratorAccess` policy.
2. An inline policy explicitly denying EC2 tag creation.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyCreatingTags",
      "Effect": "Deny",
      "Action": "ec2:CreateTags",
      "Resource": "*"
    }
  ]
}
```

### Q: Where did the administrative access come from?

**A:** It came from the attached `AdministratorAccess` managed policy. The inline policy did not grant administrative access; it removed one capability through an explicit deny.

### Q: Why did tagging fail even though the permission set included AdministratorAccess?

**A:** AWS policy evaluation gives an applicable explicit `Deny` priority over an `Allow`.

The simplified logic was:

```text
AdministratorAccess allows ec2:CreateTags
+ inline policy explicitly denies ec2:CreateTags
= final decision: DENY
```

The console returned an authorization failure such as:

```text
Client.UnauthorizedOperation
```

### Important correction

**Incorrect model:** The broadest policy or “highest” role always wins.

**Correct model:** Permissions from applicable policies are combined, but an applicable explicit deny overrides allows.

---

## 3. Public and Private Subnets

### Q: Is a public subnet simply a subnet that uses private IP ranges?

**A:** No. AWS VPC subnets normally use private RFC 1918 address ranges whether the subnet is public or private.

The public/private distinction is mainly determined by routing:

- A **public subnet** has a route such as `0.0.0.0/0 → Internet Gateway`.
- A **private subnet** does not have a direct default route to an Internet Gateway.
- A private subnet may use `0.0.0.0/0 → NAT Gateway` for outbound internet access.

### Q: Does an EC2 instance become internet-reachable merely because it is in a public subnet?

**A:** No. Several conditions must align:

1. The subnet route table must route internet traffic to an Internet Gateway.
2. The instance must have a public IPv4 address or Elastic IP for direct IPv4 internet communication.
3. The NACL must allow the required traffic in both directions.
4. The Security Group must allow the connection.
5. The operating system and application must be listening on the destination port.

### Q: If a subnet routes through a NAT Gateway, is it public?

**A:** No. A NAT Gateway allows workloads in a private subnet to initiate outbound internet connections. It does not provide direct unsolicited inbound internet access to those workloads.

---

## 4. Inbound SSH Traffic Path

The conceptual inbound path was:

```text
Windows device
→ internet
→ Internet Gateway
→ public IPv4 translated/mapped to the EC2 private IPv4
→ public subnet NACL
→ EC2 network interface Security Group
→ Linux SSH service on TCP 22
```

The reply followed the reverse direction:

```text
Linux SSH service
→ Security Group
→ NACL
→ Internet Gateway
→ Windows device
```

### Q: What does the route table do?

**A:** The route table determines the next network destination for traffic. It does not grant permission for individual TCP connections.

### Q: What is the basic difference between a Security Group and a NACL?

| Control | Attached to | State | Rule behavior |
|---|---|---|---|
| Security Group | Network interface | Stateful | Allows only; replies to allowed connections are automatically allowed |
| Network ACL | Subnet | Stateless | Supports allow and deny; request and reply directions are evaluated separately |

### Q: Can one NACL apply to multiple subnets?

**A:** Yes. One NACL can be associated with multiple subnets, but each subnet can be associated with only one NACL at a time.

---

## 5. EC2 SSH Baseline

### Resources created

- Instance name: `security-lab-ec2`
- AMI: Amazon Linux 2023
- Instance type: `t3.micro`
- VPC: `security-lab-vpc`
- Subnet: `security-lab-public-a`
- Security Group: `security-lab-ssh-sg`
- Key pair: `security-lab-key`
- SSH source: the user's current public IPv4 address as `/32`

No S3, EFS, or FSx filesystem was attached. The instance used only its default EBS root volume.

### Q: Why was the Security Group SSH source restricted to `/32`?

**A:** A `/32` IPv4 CIDR represents one IP address. This limited inbound SSH to the current public IP instead of exposing port 22 to the entire internet with `0.0.0.0/0`.

### Q: What is the default Amazon Linux SSH username?

```text
ec2-user
```

The connection command from PowerShell was:

```powershell
ssh -i ".\security-lab-key.pem" ec2-user@PUBLIC_IP
```

### Q: Why did Windows OpenSSH reject the `.pem` file?

The error stated that the private-key permissions were too open. OpenSSH ignored a private key accessible by other Windows principals.

The local NTFS permissions were restricted with:

```powershell
icacls ".\security-lab-key.pem" /inheritance:r
icacls ".\security-lab-key.pem" /grant:r "$($env:USERNAME):(R)"
```

Afterward, SSH succeeded.

### Important correction

This was not an IAM, EC2, or Security Group authorization problem. It was a local private-key file-permission problem enforced by OpenSSH.

---

## 6. Custom NACL Experiment

The original NACL was shared by public and private subnets. To avoid changing both simultaneously, a dedicated NACL was created:

```text
security-lab-public-a-nacl
```

A newly created custom NACL starts with deny-all behavior, so rules were added before associating it with the subnet.

### Baseline NACL rules for inbound SSH

**Inbound:**

```text
Rule 100: ALLOW TCP 22 from YOUR_PUBLIC_IP/32
```

**Outbound:**

```text
Rule 100: ALLOW TCP 1024-65535 to YOUR_PUBLIC_IP/32
```

### Q: Why did the outbound rule use `1024-65535` instead of port 22?

**A:** The Windows SSH client selected a temporary source port.

Example:

```text
Windows:53124 → EC2:22
EC2:22 → Windows:53124
```

For the return packet:

- Source port is `22`.
- Destination port is the Windows ephemeral port, such as `53124`.

Each new connection can use a different ephemeral port, so the NACL used an ephemeral range rather than one predictable port.

### Q: What happened when outbound NACL rule 90 denied ephemeral ports?

The temporary rule was:

```text
Rule 90: DENY TCP 1024-65535 to YOUR_PUBLIC_IP/32
Rule 100: ALLOW TCP 1024-65535 to YOUR_PUBLIC_IP/32
```

NACL rules are evaluated in ascending rule-number order. Rule `90 DENY` matched first, so rule `100 ALLOW` was never reached.

The inbound SSH request could arrive, but EC2's response could not leave the subnet. The connection failed.

After rule 90 was removed, connectivity returned.

### Important correction

**Incorrect model:** If inbound TCP 22 is allowed, SSH should work.

**Correct model:** With a stateless NACL, both the inbound TCP 22 request and the outbound response to the client's ephemeral port must be allowed.

---

## 7. Security Group Stateful Experiment

The default outbound `Allow all` rule was removed from `security-lab-ssh-sg`, while inbound SSH from the user's `/32` remained allowed.

### Q: Did a new inbound SSH connection still work with no outbound SG rule?

**A:** Yes.

The Security Group remembered the permitted inbound connection and automatically allowed its response traffic. This directly demonstrated statefulness.

### Q: Did EC2-initiated HTTPS still work?

The following command failed while the Security Group had no outbound rules:

```bash
curl --max-time 8 https://checkip.amazonaws.com
```

This HTTPS request was a new connection initiated by EC2, not a response to the inbound SSH connection. It therefore required an outbound SG rule.

### Q: Why did `curl` initially continue to fail after restoring the SG outbound allow rule?

**A:** The custom NACL was still restrictive.

For EC2-initiated HTTPS, the path was:

```text
EC2:ephemeral-port → website:443
website:443 → EC2:ephemeral-port
```

The following NACL rules were added:

**Outbound:**

```text
Rule 110: ALLOW TCP 443 to 0.0.0.0/0
```

**Inbound response:**

```text
Rule 110: ALLOW TCP 1024-65535 from 0.0.0.0/0
```

After both were added, `curl` succeeded.

### Key lesson

A flow must pass every relevant layer. Restoring the Security Group was insufficient while the NACL still blocked the path.

---

## 8. Connection Testing and Error Interpretation

PowerShell connectivity was tested with:

```powershell
Test-NetConnection PUBLIC_IP -Port 22
```

### Q: What does `TcpTestSucceeded: True` prove?

**A:** It proves that PowerShell completed a TCP connection test to the specified address and port at that moment.

### Q: What is the difference between “connection refused” and a timeout?

- **Connection refused:** Usually indicates an active TCP reset from the destination or an intermediary.
- **Timeout:** More consistent with a firewall, Security Group, or NACL silently dropping traffic.

During the lab, a temporary refusal was retested. `Test-NetConnection` returned `True`, and a subsequent SSH attempt succeeded.

### Investigation lesson

Do not assign a root cause from one transient error. Verify the destination, port, control-plane state, and repeat the test with a second tool.

---

## 9. CloudTrail Reconstruction

CloudTrail Event History was used to inspect configuration changes such as:

- `CreateNetworkAcl`
- `CreateNetworkAclEntry`
- `ReplaceNetworkAclAssociation`
- `RevokeSecurityGroupEgress`
- `AuthorizeSecurityGroupEgress`

Recent events can appear after a delivery delay, so the NACL events appeared before the newer Security Group events.

### Q: What did `userIdentity.type: AssumedRole` mean?

**A:** The API request used a temporary STS assumed-role session rather than a traditional IAM user's long-term credentials.

### Q: What did `sessionIssuer.userName` show?

It showed a generated role name similar to:

```text
AWSReservedSSO_AdministratorAccess_<suffix>
```

This connected the event to the Identity Center `AdministratorAccess` permission set.

### Q: Why did `userIdentity.arn` end in `lab-admin`?

The ARN identified both:

- The assumed role that granted authorization.
- The role-session name associated with the Identity Center user.

The event could therefore be described as:

> `lab-admin` used the Identity Center AdministratorAccess assumed-role session to call the EC2 API.

### Q: What did `sourceIPAddress` show?

It showed the user's public IP because the AWS Console API request originated through that internet connection.

### Q: What did `requestParameters.egress: false` mean?

**A:** The created NACL rule was inbound.

- `egress: false` → inbound rule
- `egress: true` → outbound rule

One inspected event contained:

```text
ruleNumber: 110
ruleAction: allow
egress: false
portRange: 1024-65535
```

That was the inbound return-traffic rule.

Another event with `egress: true` and port `443` represented the outbound HTTPS rule.

### CloudTrail versus Flow Logs

- **CloudTrail:** Who changed AWS configuration, what API was called, when, from where, and with which identity.
- **VPC Flow Logs:** Network-flow metadata such as addresses, ports, protocol, packet/byte counts, and `ACCEPT` or `REJECT`.

CloudTrail does not record individual SSH packets.

---

## 10. VPC Flow Logs and CloudWatch

A Flow Log was created on `security-lab-public-a` with:

- Filter: All
- Maximum aggregation interval: 1 minute
- Destination: CloudWatch Logs
- Log group: `/aws/vpc/security-lab-flow-logs`
- Service role: `security-lab-vpc-flow-logs-role`
- Record format: AWS default

### Q: What does the 1-minute or 10-minute option mean?

**A:** It is the maximum aggregation interval—the approximate window over which packets belonging to the same flow can be grouped into one Flow Log record.

- **1 minute:** Lower-latency visibility and potentially more records.
- **10 minutes:** More aggregation, slower visibility, and potentially fewer records.

It is not the log-retention period, and CloudWatch delivery can take additional time after the aggregation interval closes.

### Q: Is VPC Flow Log data viewed in CloudWatch?

**A:** Yes, when CloudWatch Logs is selected as the destination.

```text
VPC/Subnet/ENI traffic metadata
→ VPC Flow Logs
→ CloudWatch log group
→ log stream
→ searchable records
```

Flow Logs can alternatively publish to S3 or Data Firehose.

### Q: How was rejected traffic generated?

A temporary inbound NACL rule was added:

```text
Rule 90: DENY TCP 22 from YOUR_PUBLIC_IP/32
```

`Test-NetConnection` was run, and the deny rule was immediately removed afterward.

### Q: Why were there many unrelated `REJECT` records?

An internet-facing IP can receive unsolicited scanning and background traffic. The lab event was isolated by filtering on the user's known public source IP.

### Q: Why did one matching record show source and destination ports `0 0`?

The inspected record resembled:

```text
ACCOUNT_ID ENI_ID USER_PUBLIC_IP EC2_PRIVATE_IP 0 0 1 1 60 ... REJECT OK
```

The key fields were:

- Source: user's public IP
- Destination: EC2 private IP
- Source/destination ports: `0 0`
- Protocol: `1`
- Action: `REJECT`
- Status: `OK`

Protocol `1` is ICMP. ICMP does not use TCP or UDP ports, so the port fields were zero. `Test-NetConnection` performed an ICMP probe in addition to its TCP port test.

### Q: Why did the Flow Log show the EC2 private IP rather than its public IP?

The public IPv4 mapping occurs before traffic reaches the EC2 network interface. Flow Logs captured traffic at the VPC/subnet/ENI layer, where the instance was addressed by its private IP.

### Q: What would the TCP/SSH record look like?

The relevant portion would resemble:

```text
HIGH_SOURCE_PORT 22 6 ... REJECT OK
```

Where:

- High source port = Windows ephemeral client port
- Destination port `22` = SSH
- Protocol `6` = TCP
- `REJECT` = traffic rejected by an applicable control
- `OK` = Flow Log record was produced normally

This provided the practical answer to the earlier question about which return port SSH uses.

---

## 11. Security Group and NACL Review Questions

### Q1: The SG allows inbound TCP 22, but the NACL blocks outbound ephemeral ports. Will SSH work?

**A:** No. EC2 cannot return TCP traffic to the client's ephemeral port.

### Q2: The Security Group has inbound TCP 22 but no outbound rules. Can inbound SSH still work?

**A:** Yes. Security Groups are stateful and automatically permit response traffic for an allowed inbound connection.

### Q3: Can EC2 initiate a new outbound HTTPS connection when its SG has no outbound rules?

**A:** No. That is a new outbound flow, not reply traffic.

### Q4: If the SG permits HTTPS outbound but the NACL blocks TCP 443 outbound, will `curl` work?

**A:** No. Every applicable network-control layer must permit the path.

### Q5: Does a route to an Internet Gateway automatically permit SSH?

**A:** No. Routing provides a path; SGs, NACLs, host firewalls, and the listening service determine whether the connection succeeds.

### Q6: Why does a stateless NACL need an inbound ephemeral-port rule for EC2-initiated HTTPS?

**A:** The remote web server replies from source port 443 to the ephemeral source port originally selected by EC2. That ephemeral port becomes the inbound destination port.

### Q7: Which telemetry shows that `lab-admin` created a NACL rule?

**A:** CloudTrail.

### Q8: Which telemetry shows that a TCP or ICMP flow was accepted or rejected?

**A:** VPC Flow Logs.

---

## 12. Corrections and Strengthened Mental Models

### Correction 1: Subnet classification

**Incorrect:** Public versus private is based on whether the subnet uses public or private IP ranges.

**Correct:** Both normally use private VPC CIDRs. The route table, public-IP mapping, and controls determine internet connectivity.

### Correction 2: NACL return traffic

**Incorrect:** Allowing inbound SSH port 22 is sufficient.

**Correct:** A stateless NACL must also allow outbound traffic to the client's ephemeral destination port.

### Correction 3: Security Group return traffic

**Incorrect:** The SG must contain an outbound ephemeral-port rule for SSH replies.

**Correct:** SG state tracking automatically permits replies to an allowed inbound connection.

### Correction 4: Restoring one layer

**Incorrect:** Restoring the SG's outbound allow-all rule guarantees `curl` will work.

**Correct:** The NACL must independently permit outbound TCP 443 and inbound replies to ephemeral ports.

### Correction 5: Flow Log port zero

**Incorrect:** Ports `0 0` represented the SSH connection.

**Correct:** Protocol `1` identified ICMP, which has no TCP/UDP ports. The TCP SSH record uses protocol `6` and destination port `22`.

### Correction 6: NACL identity

**Incorrect:** A NACL associated with private subnets is inherently a “private NACL.”

**Correct:** A NACL is a reusable subnet-level rule set. The same NACL can be associated with both public and private subnets.

---

## 13. Commands Used

### SSH to Amazon Linux

```powershell
ssh -i ".\security-lab-key.pem" ec2-user@PUBLIC_IP
```

### Restrict the local private-key ACL

```powershell
icacls ".\security-lab-key.pem" /inheritance:r
icacls ".\security-lab-key.pem" /grant:r "$($env:USERNAME):(R)"
```

### Test TCP 22

```powershell
Test-NetConnection PUBLIC_IP -Port 22
```

### View the Windows ephemeral port for an established SSH connection

```powershell
Get-NetTCPConnection -RemoteAddress PUBLIC_IP -RemotePort 22 |
Select-Object LocalPort, RemotePort, State
```

### Test EC2-initiated HTTPS

```bash
curl --max-time 8 https://checkip.amazonaws.com
```

### Exit the SSH session

```bash
exit
```

---

## 14. Cleanup Performed

The following temporary resources were removed:

- EC2 instance `security-lab-ec2`
- VPC Flow Log `security-lab-public-a-flow`
- CloudWatch log group `/aws/vpc/security-lab-flow-logs`
- IAM service role `security-lab-vpc-flow-logs-role`
- Custom NACL `security-lab-public-a-nacl`
- Security Group `security-lab-ssh-sg`
- AWS key-pair record `security-lab-key`
- Local private-key file `security-lab-key.pem`

Before deleting the custom NACL, `security-lab-public-a` was reassociated with the original default NACL for `security-lab-vpc` because every subnet must remain associated with a NACL.

The VPC, subnets, route tables, and Internet Gateway were retained for future labs.

### Q: Does leaving an unused Security Group incur charges?

**A:** No. Security Groups do not have hourly or storage charges. They are often deleted after labs to prevent clutter and accidental reuse, not to stop a direct SG charge.

### Resources that deserve cost attention

- Running EC2 instances
- EBS volumes and snapshots
- NAT Gateways
- Unassociated Elastic IPs or public IPv4 usage
- Load balancers
- CloudWatch log ingestion and storage
- Data transfer

---

## 15. Demonstrated Progress

This session moved the networking material from conceptual recognition to direct observation.

Hands-on evidence included:

- Launching an Amazon Linux EC2 instance into the intended public subnet
- Restricting SSH to one public source IP
- Correcting Windows private-key permissions
- Establishing SSH successfully
- Creating and associating a dedicated custom NACL
- Breaking SSH by denying outbound ephemeral traffic
- Restoring SSH by removing the earlier NACL deny
- Removing all SG outbound rules while preserving inbound SSH replies
- Demonstrating that a new EC2-initiated HTTPS connection still required SG egress
- Identifying the NACL as the remaining blocker after the SG was restored
- Reconstructing Identity Center assumed-role activity in CloudTrail
- Distinguishing role identity, session identity, and source IP
- Creating subnet Flow Logs and sending them to CloudWatch
- Locating real rejected traffic and identifying ICMP from protocol number `1`
- Cleaning up the instance, logging resources, IAM role, NACL, SG, and keys

The remaining weakness is independent reconstruction: the behavior was understood with guidance, but should be repeated until the complete request-and-return rule set can be designed without prompts.

---

## 16. Recommended Next Lab

The next lab should cover **EC2 IAM roles and IMDSv2**:

1. Create a tightly scoped EC2 role.
2. Attach it through an instance profile.
3. Require IMDSv2.
4. Retrieve metadata using an IMDSv2 session token.
5. Observe the temporary role credentials without copying secrets into notes.
6. Use the role for one allowed and one denied AWS API action.
7. Reconstruct both events in CloudTrail.
8. Explain what happens if temporary credentials are stolen and the attacker loses access before or after expiration.

This directly continues the earlier questions about EC2 role credentials, IMDS, refresh, external use of stolen temporary credentials, and CloudTrail attribution.
