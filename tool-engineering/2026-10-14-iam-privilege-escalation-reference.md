# AWS IAM Privilege Escalation — Case-by-Case Walkthrough

Reviewed: 2026-10-14

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
