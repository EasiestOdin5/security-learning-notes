# AWS Security Lab: KMS, Secrets Manager, and Encryption Context

**Session date:** August 26, 2026  
**Status:** Completed and cleaned up  
**Region:** `us-east-1`  
**Environment:** AWS KMS, AWS Secrets Manager, IAM Identity Center, AWS CLI SSO, and CloudTrail

---

## 1. Lab Objective

The lab examined how AWS stores an application secret, controls retrieval, performs encryption and decryption, and records the activity.

The practical goals were to:

1. Create a symmetric customer-managed KMS key.
2. Store a fake API key in Secrets Manager using that key.
3. Create a narrowly scoped Identity Center permission set.
4. Prove that secret retrieval required both Secrets Manager and KMS authorization.
5. Perform an allow → deny → allow test by removing and restoring `kms:Decrypt`.
6. Inspect `GetSecretValue` and `Decrypt` events in CloudTrail.
7. Use KMS directly to encrypt and decrypt a small plaintext value.
8. Prove that a mismatched encryption context prevents decryption.
9. Remove the permission set, local files, secret, and KMS key safely.

The fake values used in this lab were not real credentials.

---

## 2. Core Architecture

The primary relationship was:

```text
Application or user
→ requests a secret from Secrets Manager
→ Secrets Manager evaluates secret access
→ KMS evaluates decryption access
→ plaintext is returned only when both gates allow
```

The two services have different responsibilities:

- **Secrets Manager** stores secret values, versions, metadata, access configuration, and rotation configuration.
- **KMS** manages protected cryptographic key material and authorizes cryptographic operations.

The KMS key itself does not store the application password or API key.

---

## 3. Customer-Managed KMS Key

A customer-managed key was created with:

- Alias: `security-lab-secrets-key`
- Key type: Symmetric
- Key usage: Encrypt and decrypt
- Key material origin: AWS KMS
- Regionality: Single-Region

The Identity Center `AdministratorAccess` role was selected as both:

- A **key administrator**, which could manage the key and policy.
- A **key user**, which could perform permitted cryptographic operations.

These are separate capabilities. Being able to configure a key does not inherently mean an identity should be able to decrypt data with it.

### Key-policy delegation

The generated key policy contained:

```json
{
  "Sid": "Enable IAM User Permissions",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::220147487340:root"
  }
}
```

In this context, the account root principal enables the account to delegate key access through IAM policies. It does not mean that only a human logged in as root may use the key.

This delegation was why an Identity Center permission-set policy containing `kms:Decrypt` could authorize the generated role to use the key.

---

## 4. Secret Creation

Secrets Manager stored the following deliberately fake value:

```json
{
  "lab_api_key": "not-a-real-secret-2026"
}
```

Configuration:

- Secret name: `security-lab/application/api-key`
- Secret type: Other type of secret
- Encryption key: `security-lab-secrets-key`
- Automatic rotation: Disabled for this introductory lab

The slash-separated secret name was an organizational naming convention, not a real folder hierarchy.

Retrieving the secret through the administrator session displayed plaintext because Secrets Manager transparently requested KMS decryption after authorization succeeded.

---

## 5. Scoped Identity Center Permission Set

A custom permission set called `SecretsLabReader` was created and assigned to `lab-admin`.

Its initial inline policy allowed:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyThisLabSecret",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:220147487340:secret:security-lab/application/api-key-*"
    },
    {
      "Sid": "DecryptWithLabKey",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:220147487340:key/fd091904-ad55-41c2-8be1-dc8ad486aebc"
    }
  ]
}
```

The Secrets Manager ARN ended in `-*` because AWS appends a generated suffix to a secret ARN. The KMS permission was restricted to the exact lab key.

An AWS CLI SSO profile named `secrets-lab-reader` was configured. `sts:GetCallerIdentity` confirmed an assumed role resembling:

```text
AWSReservedSSO_SecretsLabReader_...
```

---

## 6. Allow → Deny → Allow Test

### Initial allow

The scoped role successfully called `GetSecretValue` and returned the fake JSON value.

### Deny through missing KMS permission

The KMS statement was removed while `secretsmanager:GetSecretValue` remained allowed. The same retrieval then failed with:

```text
AccessDeniedException: Access to KMS is not allowed
```

This proved that, for a secret encrypted with this customer-managed key, effective plaintext retrieval required:

```text
secretsmanager:GetSecretValue
AND
kms:Decrypt
```

### Restored allow

The KMS statement was restored, Identity Center reprovisioned the role, and the same CLI request succeeded again.

The test produced direct evidence rather than relying only on policy interpretation.

---

## 7. What `GetSecretValue` Returns

`GetSecretValue` means “return the usable decrypted secret value.” It does not mean “return whatever bytes Secrets Manager stores.”

Secrets Manager provides:

- `DescribeSecret` for permitted metadata.
- `GetSecretValue` for decrypted secret data.
- `BatchGetSecretValue` for decrypted values from multiple secrets.

It does not expose an API for downloading its internal ciphertext representation.

If KMS decryption fails, the caller receives neither plaintext nor the internally stored ciphertext.

This hides Secrets Manager's envelope-encryption format and prevents applications from depending on an internal storage representation.

---

## 8. Security Value and Limitations

The initial observation was that Secrets Manager can appear more like password organization than security. That observation was substantially correct: central management is a major part of the value.

Centralization improves security by making secrets:

- Less likely to be committed to source code.
- Less likely to be copied among configuration files and administrator notes.
- Available through narrowly scoped workload roles.
- Auditable through CloudTrail.
- Easier to rotate, revoke, and update centrally.
- Encrypted while stored.

However, centralization also creates a valuable target. Malware controlling an application with both retrieval and decryption permission may obtain the same plaintext as the legitimate application.

Secrets Manager therefore reduces exposure and improves control; it does not make plaintext theft impossible after an authorized workload is compromised.

### Comparison with human password managers

A human password manager commonly uses one master password to derive a key that unlocks an encrypted vault containing many daily credentials.

AWS Secrets Manager uses a similar centralized-vault idea, but applications normally authenticate through IAM roles and temporary credentials rather than one human master password.

---

## 9. Direct KMS Encryption

The permission set was temporarily extended with:

```json
"kms:Encrypt"
```

A fake local plaintext was created:

```text
direct-kms-test
```

It was encrypted directly with:

```text
alias/security-lab-secrets-key
```

and this encryption context:

```text
Purpose=KmsLab
```

The CLI returned a Base64-encoded `CiphertextBlob`, which was converted into a binary file. Supplying the same encryption context to `kms:Decrypt` successfully returned the original plaintext.

Direct KMS `Encrypt` is designed for small values up to 4 KiB. Larger data normally uses envelope encryption or the AWS Encryption SDK.

---

## 10. Cryptographic Details

For the `SYMMETRIC_DEFAULT` key type, AWS KMS uses 256-bit AES-GCM-derived encryption keys internally.

- **AES-256** provides symmetric encryption with a 256-bit key.
- **GCM** provides authenticated encryption, protecting confidentiality and detecting unauthorized modification.
- KMS uses a fresh nonce and derived encryption key for encryption operations.
- The underlying KMS key material remains protected within AWS-managed hardware security modules and is not exported in plaintext.

Secrets Manager normally uses envelope encryption: a data key protects the secret, and the KMS key protects that data key.

---

## 11. Encryption Context

Encryption context is non-secret authenticated metadata bound to ciphertext.

It is not:

- A password
- A user identity
- A salt
- A replacement for IAM authorization

The distinction is:

```text
IAM and key policy
→ determine who may call Decrypt

Encryption context
→ identifies the expected data or usage context
```

When encryption used:

```text
Purpose=KmsLab
```

decryption with:

```text
Purpose=WrongValue
```

failed with:

```text
InvalidCiphertextException
```

The role had the correct ciphertext, correct key, and `kms:Decrypt`, but AES-GCM authentication failed because the supplied context differed.

Encryption context is optional for direct symmetric KMS encryption. If used, the exact key-value pairs must be supplied for decryption. It may be stored alongside ciphertext or derived from known application metadata because it is not intended to be secret.

Secrets Manager automatically used context containing:

```json
{
  "SecretARN": "arn:aws:secretsmanager:us-east-1:220147487340:secret:security-lab/application/api-key-...",
  "SecretVersionId": "..."
}
```

This bound the KMS operation to a specific secret and secret version.

Encryption context may appear in CloudTrail and must never contain sensitive values.

---

## 12. CloudTrail Evidence

The denied `GetSecretValue` event showed:

- Identity type: `AssumedRole`
- Role: `AWSReservedSSO_SecretsLabReader_...`
- Event name: `GetSecretValue`
- Secret ID: `security-lab/application/api-key`
- Result: Access denied

A successful KMS `Decrypt` event showed the Secrets Manager encryption context, including `SecretARN` and `SecretVersionId`.

The deliberately failed direct-decryption event showed:

- Event name: `Decrypt`
- Error: `InvalidCiphertextException`
- Encryption context: `Purpose=WrongValue`

CloudTrail recorded the identity, requested operation, target/context, and result without logging the secret plaintext.

---

## 13. Questions and Answers

### Is the stored value `not-a-real-secret-2026`?

Yes. It was the deliberately fake value associated with the JSON key `lab_api_key`.

### What makes Secrets Manager secure?

It reduces secret sprawl and combines encrypted storage, IAM authorization, KMS controls, central rotation, and auditability. It does not prevent an already authorized compromised application from receiving plaintext.

### Is Secrets Manager mainly password organization?

Organization is a large part of its value. IAM, KMS, auditing, and rotation turn that organization into a security control.

### Does `GetSecretValue` imply decrypted data?

Yes. It returns usable plaintext after all required authorization and decryption checks succeed.

### Can a caller retrieve Secrets Manager's ciphertext without `kms:Decrypt`?

No. Secrets Manager exposes no API for its internal encrypted representation. A KMS failure makes the complete retrieval fail.

### Can an application obtain ciphertext directly?

Yes, by sending a small plaintext value to KMS `Encrypt`, or by using envelope encryption or the AWS Encryption SDK for larger data.

### What algorithm did this symmetric KMS key use?

AWS documents AES-256-GCM-derived encryption keys for symmetric KMS cryptographic operations.

### Is encryption context a salt?

No. A salt adds variation to hashing or key derivation. Encryption context is authenticated, non-secret metadata. KMS manages the AES-GCM nonce separately.

### Does encryption context identify the right person?

No. IAM and the key policy authorize the identity. Context binds ciphertext to expected metadata or usage and can also be referenced by policy conditions.

### Must the context match for encryption and decryption?

Yes. When encryption context is supplied during encryption, identical key-value pairs are required during decryption.

### Can direct KMS encryption omit context?

Yes. Then any identity possessing the ciphertext and authorized for `kms:Decrypt` may decrypt without supplying context.

---

## 14. Cleanup

Cleanup was completed in dependency order:

1. The secret was scheduled for deletion with a seven-day recovery window.
2. The `SecretsLabReader` account assignment was removed.
3. The `SecretsLabReader` permission set was deleted.
4. The KMS key was scheduled for deletion with a seven-day waiting period.
5. Local plaintext and ciphertext test files were removed.
6. The local `secrets-lab-reader` CLI profile was removed.

Secrets and customer-managed KMS keys scheduled for deletion are not billed. The KMS key became unusable immediately upon entering `Pending deletion`. After final key deletion, ciphertext dependent on that key cannot be recovered.

---

## 15. Demonstrated Evidence

The lab provided direct evidence of the ability to:

- Create and distinguish KMS key-administrator and key-user permissions.
- Interpret account-level delegation in a KMS key policy.
- Store a fake application secret under a customer-managed key.
- Build a resource-scoped Identity Center permission set.
- Prove the intersection of Secrets Manager and KMS authorization.
- Diagnose a real KMS-related `AccessDeniedException`.
- Use direct KMS `Encrypt` and `Decrypt` operations.
- Explain AES-256-GCM, envelope encryption, nonce, salt, and encryption context at an operational level.
- Cause and diagnose `InvalidCiphertextException` through mismatched context.
- Reconstruct successful and failed activity in CloudTrail.
- Perform cost-aware cleanup of secrets, permission sets, KMS keys, CLI profiles, and local data.

The next major secrets-management evidence opportunity is workload-based retrieval and automated rotation rather than another human CLI session.
