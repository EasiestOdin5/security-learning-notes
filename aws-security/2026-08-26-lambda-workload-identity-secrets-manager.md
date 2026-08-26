# AWS Security Lab: Lambda Workload Identity and Secrets Manager

**Session date:** August 26, 2026  
**Status:** Completed and cleaned up  
**Region:** `us-east-1`  
**Environment:** AWS Lambda, IAM, Secrets Manager, KMS, CloudWatch Logs, and CloudTrail

---

## 1. Lab Objective

This lab transferred the earlier KMS and Secrets Manager authorization model from a human Identity Center session to an application workload.

The practical goals were to:

1. Restore the lab KMS key and fake secret during their recovery windows.
2. Create a dedicated Lambda execution role.
3. Grant the workload only the permissions needed to log and retrieve one secret.
4. Retrieve the secret from Python without embedding AWS credentials.
5. Remove `kms:Decrypt` and observe the application failure.
6. Restore the permission and verify recovery.
7. Correlate the failure in CloudWatch with the assumed-role identity and authorization result in CloudTrail.
8. Delete or schedule deletion of all lab resources.

No real credentials were used.

---

## 2. Workload Identity Flow

```text
Lambda function
→ assumes its IAM execution role
→ receives temporary STS credentials
→ calls Secrets Manager
→ Secrets Manager checks GetSecretValue
→ KMS checks Decrypt
→ plaintext reaches the function only when both gates allow
```

The function contained no access-key ID or secret access key. Lambda supplied temporary role credentials to the runtime automatically.

Two related ARNs appeared in CloudTrail:

- `arn:aws:iam::...:role/security-lab-lambda-secrets-role` represented the permanent IAM role definition.
- `arn:aws:sts::...:assumed-role/security-lab-lambda-secrets-role/security-lab-secret-reader` represented the temporary running session used by the function.

---

## 3. Restoring the Lab Resources

The customer-managed KMS key was still in its recovery window. Cancelling key deletion returned it to `Disabled`, after which it was explicitly enabled.

The secret initially appeared missing because the Secrets Manager console hid secrets scheduled for deletion. Enabling the relevant display setting exposed it, and deletion was cancelled.

An attempted recreation produced:

```text
A secret with this name already exists.
```

That error confirmed the original secret still existed even though the default list did not show it.

### Can the KMS key material be viewed?

No. KMS exposes the key ID, ARN, alias, policy, state, rotation settings, and audit activity, but it does not reveal the underlying symmetric key material. Authorized callers send cryptographic requests to KMS; they do not download the key.

---

## 4. Lambda Execution Role

The dedicated role was:

```text
security-lab-lambda-secrets-role
```

Its trust relationship allowed the Lambda service to assume it. The AWS-managed `AWSLambdaBasicExecutionRole` policy supplied permissions to create and write CloudWatch log streams.

An inline `ReadLabSecret` policy granted:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadLabSecret",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:220147487340:secret:security-lab/application/api-key-*"
    },
    {
      "Sid": "DecryptLabSecret",
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

The secret ARN wildcard covered Secrets Manager's generated suffix. The KMS statement targeted the exact customer-managed key.

---

## 5. Lambda Function

The function was named:

```text
security-lab-secret-reader
```

It used Python and the existing execution role. The current Lambda console placed role selection under:

```text
Additional settings → Custom execution role
```

The deployed code was:

```python
import json
import boto3

secrets = boto3.client("secretsmanager")

def lambda_handler(event, context):
    response = secrets.get_secret_value(
        SecretId="security-lab/application/api-key"
    )

    secret_data = json.loads(response["SecretString"])

    return {
        "statusCode": 200,
        "message": "Secret retrieved successfully",
        "secret_keys": list(secret_data.keys())
    }
```

The function returned only the JSON field name, not the secret value. This prevented the fake secret from being copied into test output or logs.

The successful result included:

```json
{
  "statusCode": 200,
  "message": "Secret retrieved successfully",
  "secret_keys": ["lab_api_key"]
}
```

---

## 6. Allow → Deny → Allow Test

### Initial allow

With both policy statements present, the Lambda successfully retrieved and parsed the secret.

### Deny by removing KMS permission

The entire `DecryptLabSecret` statement was removed while `secretsmanager:GetSecretValue` remained allowed. The next invocation failed with:

```text
AccessDeniedException: Access to KMS is not allowed
```

This demonstrated that successful application retrieval required both independent authorization gates:

```text
secretsmanager:GetSecretValue
AND
kms:Decrypt
```

### Restored allow

The KMS statement was restored, and the Lambda test succeeded again.

This repeated the earlier human-session authorization experiment using a workload identity, showing that the same service boundaries apply to application code.

---

## 7. CloudWatch Evidence

The function's log group was:

```text
/aws/lambda/security-lab-secret-reader
```

The failed invocation recorded the Python call site and propagated Botocore exception:

```text
[ERROR] ClientError: An error occurred (AccessDeniedException)
when calling the GetSecretValue operation: Access to KMS is not allowed
```

CloudWatch answered the application-side question:

> Where and how did the running function fail?

The log showed that `lambda_function.py` called Secrets Manager and that the SDK received an authorization failure. The secret itself was absent because the code never printed it.

---

## 8. CloudTrail Evidence

The corresponding `GetSecretValue` event showed:

- Identity type: `AssumedRole`
- Session issuer role: `security-lab-lambda-secrets-role`
- STS session suffix: `security-lab-secret-reader`
- Error code: `AccessDenied`
- Error message: `Access to KMS is not allowed`

CloudTrail answered the control-plane and data-event attribution question:

> Which AWS identity made the request, which API was called, and why was it denied?

Together, the two telemetry sources established:

```text
CloudWatch = application execution and stack trace
CloudTrail  = AWS API identity, action, resource context, and authorization result
```

The same assumed-role identity appeared in both the successful and failed API activity. Removing KMS permission changed authorization, not the workload identity.

---

## 9. Questions and Answers

### Does using a Lambda role automatically use CloudWatch?

Not merely because it is a Lambda role. In this lab, the role had `AWSLambdaBasicExecutionRole`, which granted the CloudWatch Logs write permissions. Lambda's runtime then automatically delivered invocation logs, errors, and program output.

```text
Lambda invocation
+ CloudWatch Logs permissions on the execution role
= automatic log delivery
```

Without those permissions, the function could still execute, but log delivery would fail.

### Is CloudWatch specifically for network-traffic alerts?

No. CloudWatch is AWS's general metrics, logs, dashboards, and alarms service. It can receive network metrics or VPC Flow Logs, but it does not inspect packet contents like Wireshark, Suricata, or a network IDS.

A network-related path might be:

```text
VPC Flow Logs → CloudWatch Logs → metric filter → CloudWatch Alarm
```

### Did Lambda activate CloudWatch automatically?

CloudWatch was already an available AWS service. Invoking the function caused Lambda to create and populate its log group because the execution role permitted that action. The lab did not enable CloudWatch as a whole.

### What was the “Encryption with AWS KMS” Lambda creation option?

That option protects Lambda deployment-package or configuration data with a selected KMS key. It was not required for the function to retrieve a Secrets Manager secret encrypted with the separate lab key.

### Why use a dedicated execution role?

The role defines the function's workload identity and limits its permissions independently from the human administrator who created it. This avoids embedding permanent AWS credentials and supports least privilege, revocation, and audit attribution.

---

## 10. Security Conclusions

1. Application code can access AWS services without stored access keys by using a workload role and temporary STS credentials.
2. The Lambda execution role is both an authorization boundary and the workload identity visible in audit records.
3. Secrets Manager authorization alone does not guarantee retrieval of a secret encrypted by a customer-managed KMS key.
4. Removing one required downstream permission can surface as an error on the higher-level `GetSecretValue` call.
5. Avoid returning or logging secret values; successful retrieval does not justify exposing plaintext in telemetry.
6. CloudWatch and CloudTrail are complementary: one shows runtime behavior, while the other attributes AWS API activity and authorization outcomes.

---

## 11. Cleanup

The lab was fully cleaned up:

- Deleted Lambda function `security-lab-secret-reader`.
- Deleted IAM role `security-lab-lambda-secrets-role`, including its attached and inline policies.
- Deleted CloudWatch log group `/aws/lambda/security-lab-secret-reader`.
- Scheduled `security-lab/application/api-key` for deletion with a seven-day recovery window.
- Scheduled `security-lab-secrets-key` for deletion with a seven-day waiting period.
- Retained CloudTrail events as audit evidence.

Secrets and KMS keys may remain visible while pending deletion, but they are not active for ordinary use.

---

## 12. Demonstrated Evidence

This lab directly demonstrated:

- Lambda workload identity through an assumed IAM execution role.
- Temporary STS credentials without embedded access keys.
- A least-privilege policy scoped to one secret and one KMS key.
- Python SDK integration with Secrets Manager.
- Allow → deny → allow authorization testing.
- Separate Secrets Manager and KMS permission gates.
- Safe handling that returned only secret field names.
- CloudWatch runtime-error analysis.
- CloudTrail role-session and authorization attribution.
- Correlation of application and AWS audit evidence.
- Dependency-aware cleanup of function, role, logs, secret, and key.

The workflow remained guided, so the evidence supports conservative progress increases rather than independent-mastery claims.
