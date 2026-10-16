# AWS IAM Privilege Escalation — Case-by-Case Walkthrough

**Living reference** — update as labs progress (initial review: 2026-10-14)

This reference follows the supplied notes for the Bishop Fox lab series ([part 1](https://www.youtube.com/watch?v=za_j7QvcsrY), [part 2](https://www.youtube.com/watch?v=TtoEGwhc5VE)). The core methods are valid; corrections mainly concern prerequisites and conditional outcomes. Mechanics were checked against Rhino Security Labs and AWS documentation. The videos, exact lab policies, usernames, group names, and profile labels were not independently verified; these names are retained as supplied examples. This is the supplied selection of 17 cases, not a claim that every method in either video is included.

All outcomes depend on effective permissions: administrative allow policies do not override applicable explicit denies, permissions boundaries, session policies, or organization restrictions. IAM changes can take time to propagate. `Resource: "*"` is one broad starting configuration, not a universal requirement. [2]

Commands are templates, not executed results. Replace angle-bracket placeholders with actual lab values. JSON, ZIP, script, and template files must already contain the scenario's required content. CLI profile names select credentials and configuration; they grant no permissions. Case numbers below preserve the supplied document order and may differ from lab identifiers.

---

### 1. Create Policy Version

* **Initial Setup (Starting Policy):** Permission to call `iam:CreatePolicyVersion` on a customer-managed policy attached to an identity the actor can use. The supplied lab allows `Resource: "*"`; a specifically allowed target can also be sufficient. There must be room within the five-version limit, or separate permission to delete a nondefault version.
* **Final Result (After Priv Esc):** A new version containing administrative allow permissions becomes the policy's active default. Its ID might be `v2`, but is determined by IAM.
* **AWS CLI Command:**

```bash
aws iam create-policy-version --policy-arn <policy-arn> --policy-document file://priv.json --set-as-default --profile prevask1
```

* **How It Works:** The actor changes the policy document governing attached identities. `--set-as-default` works with `iam:CreatePolicyVersion` alone; separate `iam:SetDefaultPolicyVersion` permission is unnecessary. This applies to customer-managed policies, not AWS-managed policies or inline policies. [3]

---

### 2. Set Default Policy Version

* **Initial Setup (Starting Policy):** Permission to call `iam:SetDefaultPolicyVersion` on a customer-managed policy with an existing nondefault version granting broader permissions. The policy must affect an identity the actor can use.
* **Final Result (After Priv Esc):** An existing **nondefault** administrative version, such as lowercase `v2`, becomes the active default.
* **AWS CLI Command:**

```bash
aws iam set-default-policy-version --policy-arn <policy-arn> --version-id v2 --profile prevask2
```

* **How It Works:** The action changes which saved version supplies permissions to attached identities. It does not create a policy document. Replace `v2` with the actual existing version ID; “uncommitted” is not the correct term. [3]

---

### 3. Pass Role + Run EC2

* **Initial Setup (Starting Policy):** Permissions for `iam:PassRole` on the target role and `ec2:RunInstances` on the launch resources. An instance profile must contain the same-account role, which must trust EC2. Key-pair creation (`ec2:CreateKeyPair`) is optional, not a prerequisite for user-data execution; some launch options require additional permissions.
* **Final Result (After Priv Esc):** A compatible instance executes the supplied startup code. The supplied reverse-shell scenario can give access to the instance and its temporary role credentials if networking and metadata access permit.
* **AWS CLI Command:**

```bash
aws ec2 run-instances --image-id <ami-id> --instance-type t2.micro --iam-instance-profile Name=<instance-profile-name> --user-data file://shell.sh --profile prevask3
```

* **How It Works:** EC2 receives an **instance profile**, whose name may differ from the role name. Code running on the instance can use the assigned role's credentials through IMDS; IMDSv2 requires its token flow. A reverse shell also needs a reachable listener and suitable network rules. Code can perform AWS actions locally without exporting credentials. [4][5]

---

### 4. Create Access Key

* **Initial Setup (Starting Policy):** Permission to call `iam:CreateAccessKey` on the higher-privileged IAM user. The supplied lab grants it on `*`; the target must have fewer than two existing access keys, including inactive keys.
* **Final Result (After Priv Esc):** A new active Access Key ID and Secret Access Key are created for the supplied lab's `terraform` IAM user, assuming that user exists and has broader effective permissions.
* **AWS CLI Command:**

```bash
aws iam create-access-key --user-name terraform --profile prevask4
```

* **How It Works:** The actor must use the returned credentials in subsequent requests to authenticate as `terraform`. Their original user's permissions do not change. This is IAM-user impersonation, not an STS `AssumeRole` operation; the secret is returned only when the key is created. [6]

---

### 5. Create Login Profile

* **Initial Setup (Starting Policy):** Permission to call `iam:CreateLoginProfile` on the target IAM user, which must not already have a login profile. The password must satisfy the account's password policy.
* **Final Result (After Priv Esc):** A console password is created for the supplied lab's administrative `terraform` IAM user. Console sign-in remains subject to configured MFA and other applicable authentication requirements.
* **AWS CLI Command:**

```bash
aws iam create-login-profile --user-name terraform --password <new-pass> --profile prevask5
```

* **How It Works:** Adds a console authentication method to an existing IAM user; it does not create a new AWS account or add permissions. A user without a login profile need not already have CLI keys. Creating a password does not remove MFA. [7]

---

### 6. Update Login Profile

* **Initial Setup (Starting Policy):** Permission to call `iam:UpdateLoginProfile` on a target IAM user that already has a login profile. The replacement password must meet the account password policy.
* **Final Result (After Priv Esc):** The existing console password for the supplied lab's `terraform` IAM user is replaced with a known password.
* **AWS CLI Command:**

```bash
aws iam update-login-profile --user-name terraform --password <new-pass> --profile prevask6
```

* **How It Works:** The replacement password can enable impersonation if the remaining sign-in requirements are met. The operation does not remove MFA, modify the user's permissions, or reset an IAM Identity Center user's password. [7]

---

### 7. Put Group Policy

* **Initial Setup (Starting Policy):** Permission to call `iam:PutGroupPolicy` on a group containing an IAM user the actor controls.
* **Final Result (After Priv Esc):** An inline policy named `test` is created or replaced on that group, adding the administrative allow permissions in `admin.json`.
* **AWS CLI Command:**

```bash
aws iam put-group-policy --group-name <group-name> --policy-name test --policy-document file://admin.json --profile prevask11
```

* **How It Works:** An inline policy is embedded in the group, rather than attached as a managed policy. Group members gain its allowed permissions after propagation, subject to their applicable restrictions. Modifying a group the actor cannot benefit from does not automatically elevate the actor. [1][2][8]

---

### 8. Attach Group Policy (`prevask8`)

* **Initial Setup (Starting Policy):** Permission to call `iam:AttachGroupPolicy` on the target group, with attachment of `AdministratorAccess` allowed. An IAM user controlled by the actor must belong to that group.
* **Final Result (After Priv Esc):** The AWS-managed `AdministratorAccess` policy is attached to the supplied lab's `prevask-group`.
* **AWS CLI Command:**

```bash
aws iam attach-group-policy --group-name prevask-group --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile prevask8
```

* **How It Works:** Group members receive permissions from the existing managed policy. Effective access still depends on applicable boundaries, organization policies, and denies. Group names themselves do not determine privileges. [1][2][8]

---

### 9. Attach Role Policy (`prevask9`)

* **Initial Setup (Starting Policy):** Permission to call `iam:AttachRolePolicy` on a target role, with attachment of `AdministratorAccess` allowed. The actor must already be able to use that role, or have another established path to use it.
* **Final Result (After Priv Esc):** The managed policy is attached to the underlying IAM role, expanding its allowed permissions.
* **AWS CLI Command:**

```bash
aws iam attach-role-policy --role-name <role-name> --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile prevask9
```

* **How It Works:** Attaching a policy changes the role's permissions, not its trust policy. It does not by itself make an otherwise inaccessible role assumable. The attachment is to the IAM role, not an individual STS session. [1][2]

---

### 10. Put User Policy (`prevask10`)

* **Initial Setup (Starting Policy):** Permission to call `iam:PutUserPolicy` on the actor's own IAM user, or another IAM user whose credentials they control.
* **Final Result (After Priv Esc):** An inline policy named `new-policy` is created or replaced on the supplied lab's `prevask10` IAM user.
* **AWS CLI Command:**

```bash
aws iam put-user-policy --user-name prevask10 --policy-name new-policy --policy-document file://admin.json --profile prevask10
```

* **How It Works:** The actor supplies the permissions document directly on the IAM-user object. Administrative allows can expand access after propagation, subject to applicable restrictions. A CLI profile named `prevask10` does not itself prove that the authenticated IAM user is also named `prevask10`. [1][2]

---

### 11. Put Role Policy & Assume Role (`prevask12`)

* **Initial Setup (Starting Policy):** Permission to call `iam:PutRolePolicy` on the target role and authorization to assume it with `sts:AssumeRole`. The role's trust policy and applicable conditions must allow the actor's assumption.
* **Final Result (After Priv Esc):** An inline policy grants the role broader permissions; a successful `AssumeRole` request returns temporary role credentials.
* **AWS CLI Command:**

```bash
aws iam put-role-policy --role-name <role-name> --policy-name test --policy-document file://admin.json --profile prevask12
aws sts assume-role --role-arn <role-arn> --role-session-name pwn --profile prevask12
```

* **How It Works:** The actor changes the role's permission policy, then enters that role's security context. They must use the returned Access Key ID, Secret Access Key, and Session Token for subsequent requests. The command does not automatically switch `prevask12` to the returned credentials. [1][9]

---

### 12. Add User to Group (`prevask13`)

* **Initial Setup (Starting Policy):** Permission to call `iam:AddUserToGroup` for an IAM user the actor controls and an existing group with broader permissions.
* **Final Result (After Priv Esc):** The supplied lab's `prevask13` IAM user is added to `Administrators`, if that group exists and its policies grant administrative access.
* **AWS CLI Command:**

```bash
aws iam add-user-to-group --group-name Administrators --user-name prevask13 --profile prevask13
```

* **How It Works:** The IAM user receives permissions from the group's policies after propagation, subject to applicable restrictions. IAM groups contain IAM users; an assumed-role session or IAM Identity Center user cannot be added as an IAM-group member. [1][2][8]

---

### 13. Update Assume Role Policy & Assume Role (`prevask14`)

* **Initial Setup (Starting Policy):** Permission to call `iam:UpdateAssumeRolePolicy` on the privileged target role, plus authorization for the subsequent `sts:AssumeRole` request under the resulting trust policy and other applicable policies.
* **Final Result (After Priv Esc):** The role's trust policy is changed to permit the actor, and successful assumption returns credentials for that role.
* **AWS CLI Command:**

```bash
aws iam update-assume-role-policy --role-name <role-name> --policy-document file://trust.json --profile prevask14
aws sts assume-role --role-arn <role-arn> --role-session-name pwn --profile prevask14
```

* **How It Works:** `trust.json` changes **who may assume the role**; it does not change what the role may do. A principal such as `arn:aws:iam::<account-id>:root` delegates trust to that AWS account; it does not mean the actor becomes root. Use the returned session credentials to perform actions as the role. [1][9][10]

---

### 14. Pass Role + Create & Invoke Lambda (`prevask15`)

* **Initial Setup (Starting Policy):** Permissions for `iam:PassRole`, `lambda:CreateFunction`, and `lambda:InvokeFunction` on the relevant resources. The same-account execution role must trust Lambda; the package must contain `lambda.py` with a compatible `lambda_handler` function.
* **Final Result (After Priv Esc):** The function is created and, once active, invoked using the execution role. If its code attaches an administrative policy to the actor, the role must be authorized to make that specific IAM change.
* **AWS CLI Command:**

```bash
aws lambda create-function --function-name test --runtime python3.11 --role <role-arn> --handler lambda.lambda_handler --zip-file fileb://func.zip --profile prevask15
# Invoke after the function becomes Active.
aws lambda invoke --function-name test output.txt --profile prevask15
```

* **How It Works:** The caller delegates the execution role to Lambda and runs code under that role. Creation alone does not execute the code. The supplied `python3.11` runtime is supported as of the review date; policy attachment is a payload-specific outcome, not an automatic effect of creating Lambda. [4][11]

---

### 15. Update Lambda Code (`prevask17`)

* **Initial Setup (Starting Policy):** Permission for `lambda:UpdateFunctionCode` on a function using a privileged execution role. `lambda:UpdateFunctionConfiguration` is needed only if the attack also changes configuration, such as the handler. Direct invocation additionally needs `lambda:InvokeFunction`; otherwise a working trigger must run the changed version.
* **Final Result (After Priv Esc):** The unpublished function code is replaced. When that code executes, it runs under the function's configured execution role.
* **AWS CLI Command:**

```bash
aws lambda update-function-code --function-name <func-name> --zip-file fileb://lambda.zip --profile prevask17
```

* **How It Works:** Updating code does not invoke it. Published versions are immutable; a trigger or alias targeting an older published version will not automatically run changed `$LATEST` code. The package must fit the existing runtime, handler, and architecture, and satisfy code-signing enforcement where enabled. Keeping the existing execution role does not require passing a new role. [1][12]

---

### 16. CloudFormation Stack Creation (`prevask20`)

* **Initial Setup (Starting Policy):** Permissions for `iam:PassRole` on the same-account service role and `cloudformation:CreateStack`; `cloudformation:DescribeStacks` allows reading status and outputs. The role must trust CloudFormation and have permissions for the resources and IAM changes defined in the template.
* **Final Result (After Priv Esc):** CloudFormation provisions resources using that service role. Administrative credentials appear in stack outputs only if the template explicitly creates an appropriately privileged IAM user/access key and exposes the key values in its outputs.
* **AWS CLI Command:**

```bash
aws cloudformation create-stack --stack-name pwn --template-url <template-url> --role-arn <role-arn> --capabilities CAPABILITY_NAMED_IAM --profile prevask20
# Read outputs after stack creation succeeds.
aws cloudformation describe-stacks --stack-name pwn --profile prevask20
```

* **How It Works:** The actor controls a declarative template that CloudFormation processes with the passed role's permissions. The credential outcome is template-specific, not automatic. `CAPABILITY_NAMED_IAM` acknowledges named IAM resources and also covers unnamed IAM resources; `CAPABILITY_IAM` is sufficient when no IAM resources have custom names. These flags acknowledge the template's capabilities; they do not grant IAM permissions. [13]

---

### 17. EC2 Instance Connect (`prevask21`)

* **Initial Setup (Starting Policy):** Permission for `ec2-instance-connect:SendSSHPublicKey` on a target instance for the permitted OS user. `ec2:DescribeInstances` helps discover the instance but is not intrinsic to sending a key when its details are known. The instance needs working EC2 Instance Connect integration, a valid OS user, and reachable SSH. For AWS privilege escalation, an accessible instance role must offer broader permissions.
* **Final Result (After Priv Esc):** The actor's public key is made available for SSH authentication for 60 seconds. A successful SSH login can provide access to the instance and, if available to that OS user, its role credentials.
* **AWS CLI Command:**

```bash
aws ec2-instance-connect send-ssh-public-key --instance-id <instance-id> --availability-zone <az> --instance-os-user <os-user> --ssh-public-key file://<public-key-path> --profile prevask21
# Start SSH within the public key's 60-second availability window.
ssh -i <private-key-path> <os-user>@<reachable-instance-address>
```

* **How It Works:** The API temporarily publishes a public key; it does not establish the SSH session or permanently edit `authorized_keys`. The matching private key is used by the SSH client, and OS-user and network restrictions still apply. Metadata credential access depends on the instance's configuration, including IMDSv2. Host access alone is not proof of increased AWS permissions. [5][14]

---

### CloudTrail Note

`iam:PassRole` is a permission check, not an API call, so there is no separate `PassRole` CloudTrail event. Inspect the receiving operation, such as `RunInstances`, `CreateFunction`, or `CreateStack`, and resolve the assigned role or instance profile. Legitimate administrators and automation also perform these actions; the event name alone is not proof of malicious activity. [4]

### Sources

1. [Rhino Security Labs — AWS IAM Privilege Escalation](https://github.com/RhinoSecurityLabs/AWS-IAM-Privilege-Escalation).
2. AWS: [Policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) and [IAM eventual consistency](https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot.html#troubleshoot_general_eventual-consistency).
3. AWS: [Policy versioning](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-versioning.html) and [CreatePolicyVersion API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_CreatePolicyVersion.html).
4. AWS: [Passing roles to services, including CloudTrail behavior](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html).
5. AWS: [EC2 roles and instance profiles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html) and [IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html).
6. AWS: [CreateAccessKey API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_CreateAccessKey.html) and [IAM quotas](https://docs.aws.amazon.com/general/latest/gr/iam-service.html).
7. AWS: [CreateLoginProfile API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_CreateLoginProfile.html), [UpdateLoginProfile API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_UpdateLoginProfile.html), and [IAM MFA](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html).
8. AWS: [IAM user groups](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_groups.html).
9. AWS: [Role principals and role-session credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html#principal-role).
10. AWS: [Account principals and account-root ARN semantics](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html#principal-accounts).
11. AWS: [Lambda execution roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html), [supported runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), and [CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html).
12. AWS: [UpdateFunctionCode API](https://docs.aws.amazon.com/lambda/latest/api/API_UpdateFunctionCode.html).
13. AWS: [CloudFormation service roles](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html), [CreateStack API and capability flags](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html), and [IAM access-key resource attributes](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-iam-accesskey.html).
14. AWS: [EC2 Instance Connect prerequisites](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-prerequisites.html), [connection methods](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html), and [SendSSHPublicKey API](https://docs.aws.amazon.com/ec2-instance-connect/latest/APIReference/API_SendSSHPublicKey.html).

---

## Hands-on progress and reproducible lab records

**Scope:** These entries capture only scenarios examined so far. The original 17-case reference above remains the general catalog. The policy JSON examples below are **minimal reconstructions of the effective permissions described during the labs**, not byte-for-byte exports of the original AWS policy files unless explicitly stated. Exact role/user/account resource ARNs and source JSON filenames were not consistently archived; replace placeholders with the actual lab ARN. These examples are confined to the test account; permission boundaries, SCPs and explicit denies may restrict the outcomes.

| Case | Method | Outcome | CloudTrail examined | Detector |
|---|---|---|---|---|
| 1 | CreatePolicyVersion | Hands-on completed | Yes: before/after + policy mutation | Added; positive + two negative tests |
| 2 | SetDefaultPolicyVersion | Hands-on completed | Yes: changed policy/version | Added; recent/older JSON tested |
| 4 | CreateAccessKey | Hands-on completed | Yes: new key ID correlated with subsequent API | Added; two successful events observed |
| 5 | CreateLoginProfile | Hands-on completed | Yes: CreateLoginProfile and ConsoleLogin in us-east-2 | Added; positive + negative tests |
| 6 | UpdateLoginProfile | Concept understood; lab skipped | No | Skipped |
| 7 | PutGroupPolicy | Hands-on completed | Yes: denied/mutation/successful API | Skipped deliberately |
| 8 | AttachGroupPolicy | Concept understood; lab skipped | No | Skipped |
| 9 | AttachRolePolicy | Hands-on completed | Yes: AssumeRole → temporary credential → ListUsers; original user denied | Skipped deliberately |

### Case 1 — CreatePolicyVersion

**Before:** `lab-attacker-policy` was a customer-managed policy attached to `lab-attacker`; default v1 allowed version creation but not `ListUsers`. Representative v1 document (the exact original policy resource ARN was not archived):

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:CreatePolicyVersion","Resource":"<lab-attacker-policy-arn>"}]}
```

**New policy document for v2:** Retained policy-version permission and additionally granted `iam:ListUsers`:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:CreatePolicyVersion","Resource":"<lab-attacker-policy-arn>"},{"Effect":"Allow","Action":"iam:ListUsers","Resource":"*"}]}
```

**Lab command pattern** (exact local policy document filename not preserved):

```powershell
aws iam list-users --profile lab-attacker
aws iam create-policy-version --policy-arn <lab-attacker-policy-arn> --policy-document file://policy-v2.json --set-as-default --profile lab-attacker
aws iam list-users --profile lab-attacker
```

**After:** `ListUsers` changed from `AccessDenied` to success for the same user/access key; v2 was activated as default. **Checklist:** [x] Scenario [x] Before/after verified [x] CloudTrail investigation [x] Detector [x] Positive test [x] Negative tests. [Lab record](2026-10-14-create-policy-version-lab.md).

### Case 2 — SetDefaultPolicyVersion

**Before:** Attached customer-managed `lab-attacker-policy` had an inactive v2 allowing `iam:ListUsers`; default v3 allowed `iam:SetDefaultPolicyVersion` on the policy. Representative v3:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:SetDefaultPolicyVersion","Resource":"<lab-attacker-policy-arn>"}]}
```

**Preexisting inactive v2** included `iam:ListUsers` (and, from Case 1, `iam:CreatePolicyVersion`):

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:CreatePolicyVersion","Resource":"<lab-attacker-policy-arn>"},{"Effect":"Allow","Action":"iam:ListUsers","Resource":"*"}]}
```

**Command** (policy ARN placeholder):

```powershell
aws iam set-default-policy-version --policy-arn <lab-attacker-policy-arn> --version-id v2 --profile lab-attacker
aws iam list-users --profile lab-attacker
```

**After:** v2 became default; `ListUsers` succeeded. A **fresh before-operation denial was not separately documented for Case 2**. CloudTrail `SetDefaultPolicyVersion.requestParameters.versionId` showed v2; it did not record the previous default. **Checklist:** [x] Scenario [x] Policy-version switch [x] Successful API [x] CloudTrail investigation [x] Detector [x] Recent/older data tested [ ] Fresh before-denial verified. [Lab record](2026-10-14-set-default-policy-version-lab.md).

### Case 4 — CreateAccessKey

**Before:** `lab-attacker` could not `iam:ListUsers`, but had `iam:CreateAccessKey` against `lab-privileged`. The target user had `iam:ListUsers`. Representative policy documents:

**Attacker permission:**
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:CreateAccessKey","Resource":"<lab-privileged-user-arn>"}]}
```

**Target permission:**
```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:ListUsers","Resource":"*"}]}
```

These summarize the relevant statements only; other previously granted permissions may also have existed. The actual attacker policy resource scope was **not independently verified**.

**Executed command and credential-use pattern:**

```powershell
aws iam list-users --profile lab-attacker
aws iam create-access-key --user-name lab-privileged --profile lab-attacker
# New key and secret were configured locally as profile lab-privileged-compromised.
aws iam list-users --profile lab-privileged-compromised
```

**After:** The new `lab-privileged` credential could call `ListUsers`; `lab-attacker` still could not. Correlated `CreateAccessKey.responseElements.accessKey.accessKeyId` with the subsequent `ListUsers.userIdentity.accessKeyId`—**not** the key of the user that created the credential. **Checklist:** [x] Scenario [x] Before/after [x] Credential ID correlation [x] CloudTrail [x] Detector [x] Two detections (admin setup and attacker) [ ] Automated key-use correlation. [Lab record](2026-10-15-create-access-key-lab.md).

### Case 5 — CreateLoginProfile

**Before:** `lab-privileged` had API credentials but no console login profile; `lab-attacker` had `iam:CreateLoginProfile` on that IAM user. Representative attacker permission:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:CreateLoginProfile","Resource":"<lab-privileged-user-arn>"}]}
```

**Executed command form** (actual password intentionally omitted; the user used a populated CLI JSON input file):

```powershell
aws iam create-login-profile --cli-input-json file://create-login-profile.json --profile lab-attacker
```

**Local input layout** (example only; *do not commit an actual password*):

```json
{"UserName":"lab-privileged","Password":"<redacted-password>","PasswordResetRequired":false}
```

**After:** AWS accepted the call; the user then signed into the AWS Management Console as `lab-privileged` without an MFA challenge. In CloudTrail, `CreateLoginProfile` showed attacker caller and target username. A matching `ConsoleLogin` for the target was eventually found in **`us-east-2`**, demonstrating a Region visibility gap. The two events support a sequence, not proof of which password was entered. **Checklist:** [x] Scenario [x] API success [x] Console sign-in [x] CloudTrail credential creation [x] CloudTrail login in us-east-2 [x] Detector [x] Positive and negative tests [ ] Automated correlation. [Lab record](2026-10-15-create-login-profile-lab.md).

### Case 6 — UpdateLoginProfile (concept-only)

**Before (hypothetical):** Existing IAM user with login profile and MFA configuration; attacker permitted `iam:UpdateLoginProfile` on that user. Example **not deployed**:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:UpdateLoginProfile","Resource":"<target-user-arn>"}]}
```

**Illustrative command—not executed:**

```powershell
aws iam update-login-profile --user-name <target-user> --password <replacement-password> --profile lab-attacker
```

**Expected result:** Replaces an existing console password, without disabling MFA; fails if there is no login profile. **Checklist:** [x] Concept understood [x] Compared to Case 5 [ ] Hands-on [ ] CloudTrail [ ] Detector. **Skipped intentionally due to overlap.**

### Case 7 — PutGroupPolicy

**Before:** `lab-attacker` was a member of an initially empty-permissions `Developers` IAM group and could not invoke `ListUsers`. The user's own policy permitted `iam:PutGroupPolicy` on that group. Representative user-side statement:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:PutGroupPolicy","Resource":"<Developers-group-arn>"}]}
```

**Policy document used for the group's new inline `ListUsers` policy** (reconstructed from confirmed document action; exact file bytes not archived):

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:ListUsers","Resource":"*"}]}
```

**Executed commands:**

```powershell
aws iam put-group-policy --group-name Developers --policy-name ListUsers --policy-document file://listusers.json --profile lab-attacker
aws iam list-users --profile lab-attacker
```

**After:** Command succeeded without output (expected); `lab-attacker` could now `ListUsers` by inheriting `Developers` permissions. Confirmed the group policy in the AWS Console. CloudTrail reviewed `ListUsers` denied before, `PutGroupPolicy` with actor/target/`policyDocument`, and `ListUsers` success after; same caller identity checked. **Checklist:** [x] Scenario [x] Before/after [x] Console inline policy [x] CloudTrail policy document [x] CloudTrail identity/call sequence [ ] Detector (deliberately skipped).

### Case 8 — AttachGroupPolicy (concept-only)

**Before (hypothetical):** `lab-attacker` belongs to `Developers` and has permission to attach an existing managed policy to that group:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:AttachGroupPolicy","Resource":"<Developers-group-arn>"}]}
```

**Illustrative command—not executed:**

```powershell
aws iam attach-group-policy --group-name Developers --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile lab-attacker
```

**Expected result:** The existing AWS-managed `AdministratorAccess` policy becomes attached to `Developers`; group members can receive those permissions subject to restrictions. This differs from inline `PutGroupPolicy` (supplies a policy JSON document). **Checklist:** [x] Concept understood [x] Compared to Case 7 [ ] Hands-on [ ] CloudTrail [ ] Detector. **Skipped intentionally due to overlap.**

### Case 9 — AttachRolePolicy + AssumeRole

**Before:** IAM user `lab-attacker` could not call `iam:ListUsers`. The lab role `LabAttackerSupportRole` was created without attached permission policies. Its initial trust policy selected **AWS account → This account**, represented by the account-root principal; this delegates trust to permitted principals in the account, rather than restricting assumption to the literal root user:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::220147487340:root"},"Action":"sts:AssumeRole","Condition":{}}]}
```

The user confirmed that `lab-attacker` had both `iam:AttachRolePolicy` and `sts:AssumeRole` access to the role. **Representative, reconstructed** user-side permission policy (actual deployed JSON and exact resource scope were not archived):

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["iam:AttachRolePolicy","sts:AssumeRole"],"Resource":"arn:aws:iam::220147487340:role/LabAttackerSupportRole"}]}
```

**Executed commands:**

```powershell
aws iam attach-role-policy --role-name LabAttackerSupportRole --policy-arn arn:aws:iam::aws:policy/IAMReadOnlyAccess --profile lab-attacker
aws sts assume-role --role-arn arn:aws:iam::220147487340:role/LabAttackerSupportRole --role-session-name Lab9Session --profile lab-attacker
# STS returned AccessKeyId, SecretAccessKey, and SessionToken.
# Those temporary credentials were configured locally as AWS CLI profile lab9-assumed.
aws iam list-users --profile lab9-assumed
aws iam list-users --profile lab-attacker
```

**After:** Attaching AWS-managed `IAMReadOnlyAccess` expanded the **role's** effective permissions, including `iam:ListUsers`; it did not change `lab-attacker`'s permissions or the role trust policy. Assuming the role produced temporary STS credentials and `ListUsers` succeeded using those credentials. The original IAM user continued receiving `AccessDenied`. `lab9-assumed` was a **local CLI profile name**, not an AWS identity or value recorded in CloudTrail. An initial `ListUsers` denial **under the role before the policy attachment** was not tested; the initial role had no attached permissions.

**Verified CloudTrail timeline (2026-10-16, UTC):**

| Time | API / identity | Result or evidence |
|---|---|---|
| 18:30:45 | `ListUsers` — `arn:aws:iam::220147487340:user/lab-attacker` | `AccessDenied` |
| 18:35:39 | `AssumeRole` — same IAM user | `requestParameters.roleArn` = `arn:aws:iam::220147487340:role/LabAttackerSupportRole` |
| 18:37:36 | `ListUsers` — `arn:aws:sts::220147487340:assumed-role/LabAttackerSupportRole/Lab9Session` | Success; `userIdentity.accessKeyId` matched the temporary key returned by the `AssumeRole` event |
| 18:37:52 | `ListUsers` — original `lab-attacker` | `AccessDenied` |

The user **verified the temporary-key match** between `AssumeRole.responseElements.credentials.accessKeyId` and the successful `ListUsers.userIdentity.accessKeyId`. The `AssumeRole.userIdentity.accessKeyId` is instead the original user's key. This links the original principal → STS assumption → successful role-session action. The `AttachRolePolicy` CLI operation succeeded and the managed policy attachment was confirmed in the AWS Console; **its own CloudTrail event was not separately confirmed in the recorded investigation**.

**Engineering observation:** The generic parser's `--event AssumeRole` output included many repetitive service-role events and omitted useful role-specific fields. Filtering `requestParameters.roleArn` to `LabAttackerSupportRole` located this event. This is a search/display improvement, **not** a reason to add a simplistic single-event detection.

**Checklist:** [x] Scenario [x] Successful role-policy attachment [x] AssumeRole + STS temporary credentials [x] Successful role-session API [x] Original user still denied [x] CloudTrail AssumeRole and ListUsers correlation [x] Temporary access-key match [ ] CloudTrail AttachRolePolicy separately inspected [ ] Initial role-session denial before attachment [ ] Detector (deliberately skipped).

**Next:** Case 10 `PutUserPolicy` (concept-only or hands-on decision pending). Separate tooling idea: all-Region CloudTrail collection via boto3; do not count it as a privilege-escalation case.
