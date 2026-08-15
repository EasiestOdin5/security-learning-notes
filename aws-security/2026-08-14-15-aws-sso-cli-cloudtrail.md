# AWS Security Lab: SSO, CLI, IAM, and CloudTrail

**Session date:** August 14–15, 2026  
**Status:** Hands-on session completed through testing a denied write operation  
**Environment:** AWS Console, AWS CLI v2 on Windows, IAM Identity Center, CloudTrail, and VPC

---

## 1. AWS IAM Identity Center and SSO

### Q: What are we using AWS IAM Identity Center for?

**A:** IAM Identity Center provides centralized authentication and lets a user access AWS accounts through assigned permission sets.

Instead of creating a permanent IAM user with long-term access keys, the user signs in through SSO and receives temporary credentials.

### Q: Is the SSO start URL fixed?

**A:** Yes. The organization has a fixed SSO start URL that identifies the IAM Identity Center portal.

The URL does not authenticate the user by itself. Authentication still occurs through the configured identity provider and browser session.

### Q: If I am already logged in through the browser, can the CLI use that login?

**A:** The existing browser session can make `aws sso login` complete without asking for the password again.

**Correction:** The CLI does not directly reuse the browser cookies or automatically gain access merely because the browser is logged in.

The flow is:

1. The CLI starts an SSO authorization request.
2. A browser opens.
3. The existing browser session authenticates the request.
4. AWS issues a temporary SSO token to the CLI.
5. The CLI caches that temporary token locally.

### Q: Does the CLI read my password from the password manager?

**A:** No. The AWS CLI does not retrieve the AWS password from the password manager.

The password manager or browser handles the interactive login. The CLI receives temporary tokens after authentication succeeds.

### Q: Why is this safer than saving an AWS access key?

**A:** SSO credentials are temporary and expire. The CLI does not need to permanently store the account password or a long-lived access key.

This reduces the impact of credential theft and makes centralized access removal easier.

**Correction:** The password is not necessarily stored “only in the browser.” It may be stored in the password manager. The important security property is that the CLI receives temporary credentials instead of the password.

---

## 2. Configuring AWS CLI SSO

### Q: What command configures an SSO profile?

```powershell
aws configure sso
```

### Q: What information does the CLI configuration require?

**A:** The configuration generally includes:

- SSO session name
- SSO start URL
- SSO region
- AWS account
- Permission set
- Default AWS region
- Output format
- Local CLI profile name

### Q: What does the selected permission set determine?

**A:** The permission set controls what the CLI session can do in the selected AWS account.

Examples include:

- `AdministratorAccess`
- `ReadOnlyAccess`

IAM Identity Center creates or uses an AWS role corresponding to that permission set.

### Q: What was initially confusing during setup?

**A:** Multiple accounts or permission sets were displayed, and the newest assignment did not initially appear.

After refreshing or allowing time for the assignment to propagate, the expected option became visible.

### Q: Which AWS CLI version was used?

```text
aws-cli/2.32.32
awscrt/0.29.1
Windows
```

---

## 3. Logging In Through the CLI

### Q: What command starts the CLI login?

```powershell
aws sso login --profile <profile-name>
```

### Q: What happens after running it?

**A:** The CLI opens a browser authorization flow. After the browser confirms the identity, the CLI receives and caches a temporary SSO token.

### Q: Does every AWS CLI command open the browser?

**A:** No. Once the cached SSO session is valid, subsequent commands can use it without opening the browser again.

When the session expires, `aws sso login` must be run again.

---

## 4. Verifying the Active AWS Identity

### Q: How can I verify which identity and role the CLI is using?

```powershell
aws sts get-caller-identity --profile <profile-name>
```

### Q: What does this command show?

**A:** It returns information such as:

- AWS account ID
- Principal ID
- Assumed-role ARN

The ARN indicates which IAM Identity Center permission-set role the session assumed.

### Q: Why is this verification important?

**A:** A successful login only proves authentication succeeded. It does not prove that the intended AWS account or permission set was selected.

`get-caller-identity` confirms the actual security principal being used.

---

## 5. Authentication Versus Authorization

### Q: Does successful SSO login mean the user can perform every AWS action?

**A:** No.

- **Authentication:** Establishes who the user is.
- **Authorization:** Determines which actions that authenticated session may perform.

A user can authenticate successfully but still receive `AccessDenied` for an unauthorized operation.

### Q: Can the same person have both administrative and read-only access?

**A:** Yes. The same identity can have multiple permission-set assignments.

The effective permissions depend on the AWS account and permission set selected for that session.

### Q: Can a read-only user view AWS resources?

**A:** Generally, yes. A read-only permission set allows viewing supported resources and configuration information.

It does not allow modifications such as creating, deleting, or tagging resources.

---

## 6. VPC Console Exercise

### Q: Which resource was located in the AWS Console?

**A:** The VPC named:

```text
security-lab-vpc
```

### Q: Why was the VPC initially difficult to find?

**A:** Likely causes included being on the wrong VPC page, using a different AWS region, or needing to refresh the resource list.

The VPC eventually appeared in the console.

### Q: Why does the AWS region matter?

**A:** VPCs and subnets are regional resources. A VPC created in `us-east-1` will not appear while viewing another region.

---

## 7. Testing a Write Operation

### Q: What write operation was tested?

**A:** Adding a tag to a subnet through the AWS CLI.

```powershell
aws ec2 create-tags `
  --resources <subnet-id> `
  --tags Key=CliTest,Value=Yes `
  --region us-east-1 `
  --profile <profile-name>
```

### Q: Is adding a tag considered a read operation?

**A:** No. Although a tag looks like metadata, adding or changing one modifies the AWS resource.

The relevant EC2 API action is:

```text
ec2:CreateTags
```

### Q: What error occurred?

```text
Client.UnauthorizedOperation
```

The console also reported that it failed to perform the `CreateTags` operation.

### Q: Was this failure expected?

**A:** Yes, if the active session used a read-only permission set.

The failure demonstrated that the read-only authorization boundary was working.

### Q: Does the error mean SSO or the CLI was broken?

**A:** No. The request successfully reached AWS and AWS evaluated it.

The operation failed because the active role was authenticated but not authorized to perform `ec2:CreateTags`.

---

## 8. CloudTrail: Console Versus CLI Activity

### Q: Can CloudTrail record both Console and CLI activity?

**A:** Yes. Both interfaces eventually call AWS APIs, and supported API activity can appear in CloudTrail.

### Q: How can we distinguish a Console request from a CLI request?

**A:** Useful CloudTrail fields include:

- `eventSource`
- `eventName`
- `sourceIPAddress`
- `userAgent`
- `userIdentity`
- `requestParameters`
- `errorCode`
- `errorMessage`

### Q: Why did the Console and CLI events have the same source IP?

**A:** Both requests originated from the same computer or internet connection, so they shared the same public IP address.

### Q: What field helped distinguish the CLI request?

**A:** The `userAgent` field.

The CLI event contained a value similar to:

```text
aws-cli/2.32.32 ... os/windows
```

A Console-originated request uses a browser or AWS Console-related user agent instead.

### Q: What does this demonstrate for incident investigation?

**A:** Source IP alone may not identify which tool performed an action.

Investigators should correlate multiple fields, especially:

- Role and session identity
- User agent
- Event name
- Request parameters
- Timestamp
- Source IP
- Success or failure status

---

## 9. What the Unauthorized Event Teaches Us

### Q: Why is a denied request still useful security telemetry?

**A:** A denied operation can show:

- Who attempted the action
- Which role was active
- What resource was targeted
- Which API action was attempted
- Where the request originated
- Why AWS rejected it

### Q: What does `Client.UnauthorizedOperation` tell us?

**A:** AWS received the API request but the active principal lacked permission to perform it.

This is different from:

- An invalid CLI command
- A network failure
- An expired SSO session
- A missing AWS resource

### Q: Why should denied events be monitored?

**A:** Repeated or unusual denied actions can reveal:

- User mistakes
- Incorrect role assignments
- Misconfigured automation
- Unauthorized discovery attempts
- A compromised identity attempting privilege escalation

---

## 10. Important Corrections and Clarifications

### Correction 1: Browser login and CLI access

**Incorrect mental model:**

> If the browser is logged in, the CLI automatically has access.

**Correct model:**

> The CLI must initiate its own SSO authorization flow. The existing browser session can approve that flow without requiring another password entry.

### Correction 2: Where credentials reside

**Incorrect mental model:**

> The password exists only in the browser.

**Correct model:**

> The password may be stored by a password manager, but the CLI does not need to retrieve it. The CLI stores temporary SSO tokens and credentials.

### Correction 3: Tags and read-only access

**Incorrect mental model:**

> A tag is only descriptive information, so read-only access might allow it.

**Correct model:**

> Creating or modifying a tag changes the resource’s metadata and requires a write permission such as `ec2:CreateTags`.

### Correction 4: Authentication and permissions

**Incorrect mental model:**

> A successful login means the AWS operation should succeed.

**Correct model:**

> Login proves authentication. Each requested AWS API action is separately evaluated for authorization.

---

## 11. Commands Reviewed

### Configure SSO

```powershell
aws configure sso
```

### Start an SSO session

```powershell
aws sso login --profile <profile-name>
```

### Confirm the active principal

```powershell
aws sts get-caller-identity --profile <profile-name>
```

### Attempt to tag a subnet

```powershell
aws ec2 create-tags `
  --resources <subnet-id> `
  --tags Key=CliTest,Value=Yes `
  --region us-east-1 `
  --profile <profile-name>
```

### Check the AWS CLI version

```powershell
aws --version
```

---

## 12. Topics Covered

- AWS IAM Identity Center
- Browser-based SSO
- AWS CLI SSO profiles
- Temporary credential caching
- Permission sets
- Assumed roles
- Authentication versus authorization
- Administrative versus read-only access
- AWS regions
- VPC and subnet identification
- Resource tagging
- Expected authorization failures
- CloudTrail event investigation
- Console-versus-CLI attribution
- Least privilege

---

## 13. Demonstrated Progress

Before this exercise, several parts of AWS SSO and CLI access were mainly conceptual.

By the end of the exercise, the following were demonstrated hands-on:

- Configuring an AWS CLI SSO profile
- Authenticating the CLI through a browser flow
- Understanding that the CLI receives temporary credentials
- Selecting an AWS account and permission set
- Verifying the active caller identity
- Locating a VPC in the correct region
- Comparing Console and CLI CloudTrail activity
- Recognizing a read-only authorization failure as expected behavior
- Distinguishing authentication success from authorization failure

This is evidence of practical improvement in modern identity and AWS security fundamentals, although more repetition is needed before treating the skills as independently operational.

---

## 14. Current Stopping Point

The read-only CLI session attempted to add a tag and received:

```text
Client.UnauthorizedOperation
```

This confirmed that the permission boundary was functioning.

A logical continuation would be to locate the denied `CreateTags` event in CloudTrail and reconstruct:

1. Who made the request
2. Which permission-set role was active
3. Which subnet was targeted
4. Which fields identify the CLI
5. How the denial appears in `errorCode` and `errorMessage`

---

## Appendix: GitHub Learning-Repository Setup

### Q: Is GitHub now accessible from ChatGPT?

**A:** Yes. Access was verified for the connected account:

```text
EasiestOdin5
```

The learning repository is:

```text
EasiestOdin5/security-learning-notes
```

Its default branch is:

```text
main
```

### Q: Which ChatGPT plugin permission was selected?

**A:** `Allow read actions`

This allows repository inspection without repeated approval prompts. Changes still require approval.

### Q: What was the important distinction during setup?

**A:** The ChatGPT plugin permission page controls when ChatGPT asks before actions. GitHub’s installed-app configuration controls which repositories the connector can access.
