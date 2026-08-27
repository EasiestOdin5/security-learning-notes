# Kubernetes Security Lab: Workload Identity, RBAC, and Service-Account Token Hardening

**Session date:** August 26–27, 2026  
**Status:** Completed and cleaned up  
**Environment:** Windows 11, Docker Desktop, Minikube, Kubernetes v1.35.1, and `kubectl` v1.36.1  
**Cloud dependency:** None; the lab ran entirely on the local computer

---

## 1. Lab Objective

This lab examined how a Kubernetes workload authenticates to the control plane and how RBAC decides what that workload may do.

The practical goals were to:

1. Start and verify a local Minikube cluster.
2. Create an isolated namespace.
3. Create a service account as a pod workload identity.
4. Create a namespace-scoped Role without assigning it.
5. Connect the service account to the Role with a RoleBinding.
6. Test allowed and denied permissions with `kubectl auth can-i`.
7. Create a real pod using the service account.
8. Call the Kubernetes API from inside the pod using its projected token.
9. Prove that pod access was allowed while Secret access was denied.
10. Delete and restore the RoleBinding to demonstrate allow → deny → allow.
11. Prove that the permission did not cross namespace boundaries.
12. Disable automatic token mounting in a second pod.
13. Delete the lab namespace and all contained resources.

---

## 2. Local Cluster Selection

The installed prerequisites were verified:

```text
Docker Desktop 4.83.0
Docker Engine 29.6.2
kubectl v1.36.1
Minikube Kubernetes v1.35.1
```

The existing Minikube context was selected. `kind` was not installed and was unnecessary because Minikube already provided the local cluster.

The cluster was initially stopped, then started with Docker:

```powershell
minikube start --driver=docker
```

Verification showed:

```text
current context: minikube
node: minikube
status: Ready
role: control-plane
```

### Why use Minikube instead of EKS?

The goal was to learn Kubernetes-native service accounts and RBAC without simultaneously introducing AWS IAM, EKS access entries, VPC networking, worker-node configuration, and cloud cost.

Minikube did not interact with AWS. It ran the control plane, node, pods, service accounts, and RBAC resources locally. It could access the internet to download container images.

Kubernetes RBAC belongs to Kubernetes itself and applies to Minikube, self-managed clusters, EKS, AKS, and GKE.

---

## 3. Existing Cluster Workloads

The cluster already contained:

- Kubernetes system components in `kube-system`.
- Falco components in `falco`.
- Earlier `attack-pod` and DVWA workloads in `default`.

These were preserved. A separate namespace kept the new lab isolated:

```powershell
kubectl create namespace rbac-lab
```

The `default` namespace is where Kubernetes places namespaced resources when no namespace is specified. The new namespace prevented this lab from interfering with the existing DVWA and Falco work.

---

## 4. Service Account: Workload Identity

The service account was created with:

```powershell
kubectl create serviceaccount lab-reader --namespace rbac-lab
```

`lab-reader` was a Kubernetes workload identity, not a human user and not a Linux account inside the container.

Kubernetes does not normally store human `User` objects. Human authentication comes from an external mechanism. In EKS, an AWS IAM principal can authenticate through an EKS access entry and then receive Kubernetes authorization through an EKS access policy or Kubernetes RBAC.

Every pod is assigned a service account. If none is specified, the pod uses the namespace's `default` service account.

Before any custom RBAC assignment, the authorization check returned `no`:

```powershell
kubectl auth can-i get pods `
  --as=system:serviceaccount:rbac-lab:lab-reader `
  --namespace=rbac-lab
```

The `--as` option impersonated the identity for an authorization check. It did not obtain the token or perform the requested resource operation.

---

## 5. Role: Permission Definition

The Role was created with:

```powershell
kubectl create role pod-reader `
  --verb=get,list `
  --resource=pods `
  --namespace=rbac-lab
```

The Role defined:

```text
Resource: pods
Verbs: get, list
Scope: rbac-lab namespace
```

Creating the Role alone did not grant it to anyone. Repeating the authorization check still returned `no`.

This established the distinction:

```text
Role        = what actions are permitted
RoleBinding = who receives those permissions
```

This is similar to creating an AWS Identity Center permission set without assigning it to a user or group.

---

## 6. RoleBinding: Identity-to-Permission Assignment

The binding was created with:

```powershell
kubectl create rolebinding lab-reader-pod-reader `
  --role=pod-reader `
  --serviceaccount=rbac-lab:lab-reader `
  --namespace=rbac-lab
```

The name `lab-reader-pod-reader` was a custom descriptive name for the RoleBinding object. Kubernetes did not require that naming pattern.

The complete relationship was:

```text
lab-reader ServiceAccount
→ lab-reader-pod-reader RoleBinding
→ pod-reader Role
→ get/list pods in rbac-lab
```

After the binding existed, the same `get pods` authorization check returned `yes`.

A separate `delete pods` check would return `no`; `kubectl auth can-i` asks an authorization question and does not delete a real pod.

---

## 7. Real Workload Pod

The first pod used the service account:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: identity-test
  namespace: rbac-lab
spec:
  serviceAccountName: lab-reader
  containers:
    - name: test
      image: alpine:3.20
      command: ["sleep", "86400"]
  restartPolicy: Never
```

The `sleep` command kept the otherwise idle test container running so commands could be executed inside it. The first version used `3600` seconds and completed before a later test, so the disposable pod was recreated with `86400` seconds.

The pod's service-account assignment was verified as `lab-reader`.

---

## 8. Projected Service-Account Files

Kubernetes injected a projected credential volume into the first pod at:

```text
/var/run/secrets/kubernetes.io/serviceaccount/
```

The mounted files included:

- `token`: a short-lived credential identifying `lab-reader`.
- `ca.crt`: the certificate authority used to verify the Kubernetes API server.
- `namespace`: the pod's `rbac-lab` namespace.

The files were not embedded in the Alpine image. The control plane issued and validated the service-account identity, while the node's kubelet mounted the projected files into the container.

The directory name contains `secrets`, but these projected files were not ordinary Kubernetes Secret objects obtained from the `/secrets` API.

The token itself was never printed or copied into the notes.

---

## 9. Kubernetes API Server

Inside a cluster, pods normally reach the API server through:

```text
https://kubernetes.default.svc
```

Breakdown:

- `kubernetes`: Service name.
- `default`: namespace containing the Service.
- `svc`: Kubernetes service DNS domain.

The API server is the front door of the control plane. It authenticates requests, invokes authorization such as RBAC, applies admission controls, and coordinates access to cluster state.

Other control-plane components include `etcd`, `kube-scheduler`, and `kube-controller-manager`, but the pod called `kube-apiserver` through the internal Service.

The built-in namespaced API paths used were:

```text
/api/v1/namespaces/rbac-lab/pods
/api/v1/namespaces/rbac-lab/secrets
```

The existence of an API resource does not imply permission to use it.

---

## 10. Allowed API Request

`curl` was installed in the disposable Alpine container. It then made a real HTTPS request from inside the pod using the mounted token and CA certificate.

The request to list pods returned:

```json
{
  "kind": "PodList",
  "apiVersion": "v1"
}
```

The complete allowed path was:

```text
pod reads mounted token
→ API authenticates system:serviceaccount:rbac-lab:lab-reader
→ RBAC finds RoleBinding
→ pod-reader permits list pods
→ API returns PodList
```

Unlike `kubectl auth can-i`, this was an actual read request made by the workload.

---

## 11. Denied Secret Request

The same pod, token, certificate, and API server were used to request the `secrets` resource. Kubernetes returned:

```text
status: Failure
reason: Forbidden
code: 403
message: User "system:serviceaccount:rbac-lab:lab-reader"
         cannot list resource "secrets" in namespace "rbac-lab"
```

This proved:

- Authentication succeeded because Kubernetes identified `lab-reader`.
- Authorization failed because the Role allowed only `pods`.
- `403 Forbidden` represented an authenticated identity lacking permission.

Kubernetes Secrets can store application passwords, API keys, TLS private keys, registry credentials, and similar small sensitive values. Ordinary workloads should not normally have broad `list secrets` permission. Applications often receive only a specifically referenced Secret as a mounted file or environment value instead of direct permission to enumerate every Secret.

Modern projected service-account tokens are distinct from ordinary Secret objects, although older Kubernetes versions commonly stored long-lived service-account tokens as Secrets.

---

## 12. Allow → Deny → Allow Through RoleBinding

The RoleBinding was deleted while the service account, Role, and pod remained:

```powershell
kubectl delete rolebinding lab-reader-pod-reader --namespace rbac-lab
```

The previously successful pod-list request then returned `403 Forbidden`.

This isolated the authorization dependency:

```text
valid token + existing Role + no RoleBinding = no assigned permission
```

The RoleBinding was recreated with the same identity and Role. The pod-list request succeeded again, completing allow → deny → allow.

---

## 13. Namespace Boundary

The `lab-reader` authorization check for listing pods in `default` returned `no` even though the identity could list pods in `rbac-lab`.

This demonstrated:

```text
rbac-lab pods → allowed
default pods  → denied
```

A `Role` and `RoleBinding` are namespace-scoped. A `ClusterRole` and appropriate binding are required when permissions must apply at cluster scope or across namespaces.

---

## 14. Inspecting Stored RBAC Objects

`kubectl describe` showed:

```text
Role pod-reader:
  Resources: pods
  Verbs: get, list

RoleBinding lab-reader-pod-reader:
  Role: pod-reader
  Subject: ServiceAccount lab-reader in rbac-lab
```

The empty `Resource Names` field meant the Role applied to all pods in `rbac-lab`, not only to a specifically named pod.

---

## 15. Tokenless Pod Hardening

A second pod was created with:

```yaml
serviceAccountName: lab-reader
automountServiceAccountToken: false
```

The pod ran normally, but listing the standard service-account path produced:

```text
ls: /var/run/secrets/kubernetes.io/serviceaccount: No such file or directory
```

This was the expected evidence. Kubernetes did not mount the projected token, CA certificate, or namespace files.

The security purpose was concrete:

```text
Compromise identity-test
→ attacker may steal mounted lab-reader token
→ attacker can use permissions granted to lab-reader

Compromise tokenless-test
→ no automatically mounted token to steal
→ attacker cannot normally authenticate as lab-reader
```

The tokenless pod could still reach the API server over the network. The setting removed automatic credentials; it was not a network firewall. A request without another valid credential would normally receive `401 Unauthorized`, whereas a valid identity lacking RBAC permission receives `403 Forbidden`.

This setting is appropriate for workloads that do not need to call the Kubernetes API.

---

## 16. Cleanup

All lab resources were namespaced, so one command removed them:

```powershell
kubectl delete namespace rbac-lab
```

This deleted:

- `identity-test` pod.
- `tokenless-test` pod.
- `lab-reader` service account.
- `pod-reader` Role.
- `lab-reader-pod-reader` RoleBinding.
- The `rbac-lab` namespace itself.

Resources in `default`, `falco`, and `kube-system` were not affected. Minikube itself was preserved.

---

## 17. Questions and Answers Summary

### Does Kubernetes RBAC apply to a local computer?

Yes. RBAC controls Kubernetes API authorization in any Kubernetes cluster, including Minikube running locally. It does not control general Windows permissions.

### Can Kubernetes users be linked to AWS identities in EKS?

Kubernetes does not create ordinary human User objects. In EKS, an IAM user or role can authenticate through an EKS access entry and then receive Kubernetes permissions through EKS access policies or Kubernetes RBAC. Kubernetes service accounts are workload identities and can separately be associated with AWS workload roles.

### What is a pod's identity?

It is the service account the pod uses when authenticating to the Kubernetes API. It is separate from the Linux user inside the container.

### Do pods require a service account?

Every pod is assigned one. If none is specified, Kubernetes uses the namespace's `default` service account. A pod may not need to use its identity if it never calls the Kubernetes API.

### Are the mounted token files Kubernetes Secrets?

Not in this modern projected-token workflow. They are files from a projected service-account volume. Ordinary Kubernetes Secret objects are available through the separate `/secrets` API when authorized.

### Does disabling token mounting block the API server?

No. The pod may still have network connectivity to the API server, but it lacks the normal service-account credential used to authenticate.

---

## 18. Demonstrated Evidence

This lab directly demonstrated:

- Starting and verifying a local Kubernetes cluster.
- Preserving existing namespaces and workloads.
- Creating and isolating a lab namespace.
- Creating a service-account workload identity.
- Distinguishing Role definitions from RoleBinding assignments.
- Testing authorization before and after binding.
- Running a pod under a dedicated service account.
- Identifying projected token, CA, and namespace files without exposing the token.
- Calling the Kubernetes API server from inside a pod.
- Distinguishing `200`, `401`, and `403` conceptually.
- Allowing pod reads while denying Secret enumeration.
- Removing and restoring authorization by deleting and recreating the RoleBinding.
- Enforcing namespace scope.
- Inspecting live Role and RoleBinding configuration.
- Preventing default credential injection with `automountServiceAccountToken: false`.
- Cleaning up all lab resources through namespace deletion.

The lab was guided and required clarification of several concepts and command behaviors. It nevertheless produced broad, direct evidence across workload identity, RBAC evaluation, API interaction, failure testing, namespace boundaries, and token hardening.
