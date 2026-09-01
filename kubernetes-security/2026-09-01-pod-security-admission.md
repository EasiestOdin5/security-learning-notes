# Kubernetes Security Lab: Pod Security Admission

**Session date:** August 31–September 1, 2026

**Status:** Completed and cleaned up

**Environment:** Windows 11, Docker Desktop, Minikube, Kubernetes v1.35.1, and `kubectl` v1.36.1

**Cloud dependency:** None; the lab used the original local `minikube` cluster

---

## 1. Objective

This lab tested how Kubernetes prevents insecure pods from being created instead of relying on every developer to harden each workload correctly. It compared baseline and restricted Pod Security Standards, tested admission outcomes, configured enforcement/warning/audit behavior, demonstrated non-retroactive tightening, and pinned rule versions.

---

## 2. Cluster and Namespace Setup

The original Minikube control plane, kubelet, API server, and kubeconfig were running, and the current context was `minikube`.

Unlike the NetworkPolicy lab, no separate cluster was needed. NetworkPolicy required a Calico-enabled CNI, while Pod Security Admission is built into the Kubernetes API server. Two namespaces were sufficient:

```powershell
kubectl create namespace psa-baseline
kubectl create namespace psa-restricted
```

Initial enforcement was enabled with namespace labels:

```powershell
kubectl label namespace psa-baseline pod-security.kubernetes.io/enforce=baseline
kubectl label namespace psa-restricted pod-security.kubernetes.io/enforce=restricted
```

The current context remained `minikube`; `--namespace` selected a namespace inside the cluster without changing clusters.

---

## 3. Built-in Pod Security Standards

| Level | Purpose |
|---|---|
| `privileged` | Almost unrestricted; for trusted workloads requiring host-level access |
| `baseline` | Blocks known privilege-escalation risks while remaining compatible with many applications |
| `restricted` | Requires stronger hardening for ordinary security-sensitive workloads |

These standards are built into Kubernetes but are not automatically enforced on ordinary namespaces. The levels cannot be edited or blended. Custom requirements can be added through Kubernetes `ValidatingAdmissionPolicy`, Kyverno, or OPA Gatekeeper.

---

## 4. Privileged Pod Rejected by Baseline

The first manifest requested a privileged BusyBox container:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: privileged-test
spec:
  containers:
    - name: test
      image: busybox:1.36.1
      command: ["sleep", "86400"]
      securityContext:
        privileged: true
```

Applying it to `psa-baseline` returned:

```text
Forbidden: violates PodSecurity "baseline:latest": privileged
container "test" must not set securityContext.privileged=true
```

The API server rejected the Pod object before scheduling or container startup. Privileged mode grants broad access to kernel interfaces and devices, so it violates both baseline and restricted.

---

## 5. Baseline-Compatible but Restricted-Incompatible

A second manifest removed privileged mode but did not add hardening:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: baseline-compatible
spec:
  containers:
    - name: test
      image: busybox:1.36.1
      command: ["sleep", "86400"]
```

It was admitted in `psa-baseline`. The same manifest was rejected in `psa-restricted` for four reasons:

```text
allowPrivilegeEscalation != false
capabilities.drop does not contain ALL
runAsNonRoot != true
seccompProfile was not RuntimeDefault or Localhost
```

Runtime verification in the baseline namespace returned `uid=0(root)`. This proved baseline blocks clearly dangerous settings but still permits root containers.

---

## 6. Restricted-Compatible Pod

The manifest was hardened:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-compatible
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: test
      image: busybox:1.36.1
      command: ["sleep", "86400"]
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop:
            - ALL
```

The pod was admitted into `psa-restricted`, and `id` returned UID 1000. `runAsUser: 1000` ensured BusyBox actually started as non-root.

Restricted requires all Linux capabilities to be dropped and permits only `NET_BIND_SERVICE` to be added back. These are Linux capabilities, which divide traditional root authority into smaller privileges.

---

## 7. Enforce, Warn, and Audit

Restricted warning mode was added to the baseline namespace:

```powershell
kubectl label namespace psa-baseline pod-security.kubernetes.io/warn=restricted
```

An unhardened `warning-test` pod passed enforced baseline and was created, but the submitting user immediately received warnings for all four restricted violations.

Audit mode was then added:

```powershell
kubectl label namespace psa-baseline pod-security.kubernetes.io/audit=restricted
```

| Mode | Effect |
|---|---|
| `enforce` | Rejects requests that violate the selected level |
| `warn` | Returns immediate violation warnings without blocking |
| `audit` | Adds violation details to Kubernetes audit-event metadata without blocking or warning by itself |

With `enforce=baseline`, `warn=restricted`, and `audit=restricted`:

- A baseline violation was rejected.
- A pod passing baseline but failing restricted was admitted with a warning and audit annotation.
- A pod satisfying restricted was admitted without Pod Security warnings.

Audit supports SOC, platform, security, compliance, and incident-response teams, but Kubernetes audit logging must be enabled and collected. The namespace label alone does not create an audit-log pipeline.

---

## 8. Tightening Is Not Retroactive

The baseline namespace was tightened:

```powershell
kubectl label namespace psa-baseline pod-security.kubernetes.io/enforce=restricted --overwrite
```

Kubernetes warned that its two existing root pods violated restricted but left them running. Pod Security Admission evaluates creation and relevant updates; it does not mutate, terminate, or convert existing pods.

A new unhardened `after-tightening` pod was rejected for the four restricted violations. If an existing noncompliant pod were deleted and a controller attempted to recreate it, admission could reject the replacement.

---

## 9. Version Pinning

Enforcement was pinned to the cluster's Kubernetes minor version:

```powershell
kubectl label namespace psa-baseline psa-restricted pod-security.kubernetes.io/enforce-version=v1.35
```

Warning and audit evaluation were also pinned:

```powershell
kubectl label namespace psa-baseline pod-security.kubernetes.io/warn-version=v1.35 pod-security.kubernetes.io/audit-version=v1.35
```

Without explicit version labels, `latest` is used and behavior may change after an upgrade. Pinning makes changes deliberate and predictable.

Final state:

| Namespace | Enforce | Warn | Audit |
|---|---|---|---|
| `psa-baseline` | `restricted:v1.35` | `restricted:v1.35` | `restricted:v1.35` |
| `psa-restricted` | `restricted:v1.35` | Not configured | Not configured |

The name `psa-baseline` described its original purpose but no longer controlled policy; only current labels did.

---

## 10. Questions and Answers

### Do we define baseline ourselves?

No. It is a built-in standard selected through namespace labels. Custom requirements need another admission-policy mechanism.

### Is baseline enforced by default?

No. It is built in but generally must be activated through namespace labels or cluster-wide admission defaults.

### Can we create a level between the built-in levels?

Not by modifying them. A platform can combine Pod Security Admission with `ValidatingAdmissionPolicy`, Kyverno, or OPA Gatekeeper.

### Would removing `privileged: true` make a pod pass restricted?

No. It made the test pass baseline, but restricted also required no privilege escalation, dropped capabilities, non-root execution, and seccomp.

### Are these Linux capabilities?

Yes. Restricted requires dropping all Linux capabilities and permits only `NET_BIND_SERVICE` to be added back.

### What are BusyBox and Alpine?

Both are small Linux container images. BusyBox bundles basic Unix commands into a tiny executable for simple tests. Alpine is a small distribution with a package manager and a more complete environment.

### Were these beginner questions?

The image, container, and pod questions were foundational. The admission-policy, failure-testing, capability, and governance reasoning was beyond beginner-level security reasoning. The primary gap was Kubernetes operational vocabulary rather than security fundamentals.

### What is the difference between warn and audit?

Warn gives immediate feedback to the developer submitting the request. Audit preserves violation metadata for later centralized review by security and operations teams.

### Can warn and audit work together?

Yes. They are independent labels and can be combined with any enforcement level.

### How did one label command target multiple namespaces?

The command follows:

```text
kubectl label namespace <namespace1> <namespace2> <key=value>
```

The positional names identify namespace resources; `key=value` is applied to each. Namespace names cannot contain `=`, so the syntax is unambiguous. Pod Security Admission recognizes the reserved `pod-security.kubernetes.io/...` keys.

### Did tightening change existing pods?

No. Existing pods retained their specifications and continued running. New creations and relevant updates became subject to restricted enforcement.

---

## 11. Security Model

```text
Developer submits Pod YAML
          ↓
API server runs Pod Security Admission
          ↓
enforce may reject | warn may notify | audit may annotate
          ↓
Only admitted specifications reach scheduling and runtime
```

Pod Security Admission is preventive control at the API boundary. It complements RBAC, NetworkPolicy, workload security contexts, and runtime monitoring.

---

## 12. Cleanup

Both namespaces and all contained pods and labels were deleted:

```powershell
kubectl delete namespace psa-baseline psa-restricted
```

The three local manifests were removed. The original Minikube cluster remained running and unchanged outside the deleted namespaces.

---

## 13. Key Takeaways

- Pod Security Admission is built in, but namespace enforcement is normally opt-in.
- Baseline blocks major dangerous configurations while still permitting root.
- Restricted requires explicit hardening and prevents insecure manifests before runtime.
- Enforce, warn, and audit serve different audiences and can operate together.
- Admission changes are not retroactive.
- Policy level and policy version are separate labels.
- Namespace names are descriptive; labels determine admission behavior.
