# Kubernetes Security Lab: NetworkPolicy and Pod Hardening

**Session date:** August 27–30, 2026

**Status:** Completed and cleaned up

**Environment:** Windows 11, Docker Desktop, Minikube, Kubernetes v1.35.1, `kubectl` v1.36.1, and Calico
**Cloud dependency:** None; the lab ran in a separate local Minikube profile

---

## 1. Lab Objective

This lab examined two complementary Kubernetes security layers:

1. **NetworkPolicy:** which pods may communicate with a workload.
2. **Pod hardening:** what a process may do after it starts or is compromised.

The practical goals were to create a Calico-enabled cluster, prove the default allow-all network behavior, enforce default-deny ingress, add a label-based allow exception, and verify Linux workload restrictions from inside a hardened pod.

---

## 2. Cluster and CNI Preparation

The existing `minikube` profile used a basic bridge CNI configuration. No Calico, Cilium, Antrea, or Weave components were running, so a second independent Minikube profile was created to ensure NetworkPolicy enforcement without disturbing the existing DVWA and Falco workloads.

```powershell
minikube start --profile netpol-lab --driver=docker --cni=calico
```

The new cluster and its active context were both named `netpol-lab`. Calico enforcement was verified through its running node and controller components.

A namespace also named `netpol-lab` was created inside that cluster. The identical names were legal but represented different objects:

```text
Minikube profile/cluster: netpol-lab
└── Kubernetes namespace: netpol-lab
```

### CNI concepts clarified

- CNI means **Container Network Interface**.
- It attaches pods to the cluster network, assigns pod IP addresses, and may enforce policy.
- A useful analogy is DHCP plus virtual switching/routing and optional firewall enforcement.
- It is not exactly an AWS VPC: a VPC is the network environment, while a CNI implements pod networking.
- Containers in one pod share the pod's network namespace, IP address, and port space and communicate through `localhost`.
- Standard NetworkPolicy needs a CNI implementation that enforces it.

---

## 3. Test Workloads and Service Discovery

An isolated namespace was created:

```powershell
kubectl create namespace netpol-lab
```

Three pods were used:

| Pod | Image/purpose | Label |
|---|---|---|
| `web` | Nginx destination on TCP/80 | `app=web` |
| `allowed-client` | Curl test client | `access=allowed` |
| `blocked-client` | Curl test client | `access=blocked` |

The curl pods ran `sleep 86400` so they stayed alive for 24 hours and accepted later `kubectl exec` commands. The public `curlimages/curl` image was used as a troubleshooting client, not as a permanent application architecture.

A Service gave the Nginx pod a stable internal name:

```powershell
kubectl expose pod web --port=80 --name=web --namespace=netpol-lab
```

Within the same namespace, Kubernetes DNS resolved `http://web` to the Service. The Service name and pod name did not have to match. A public name such as `something.com` would require external DNS and an Ingress or another cluster entry point.

---

## 4. Baseline: Both Clients Allowed

Before any NetworkPolicy existed, both clients successfully received the Nginx page:

```powershell
kubectl exec allowed-client --namespace=netpol-lab -- curl --max-time 5 http://web
kubectl exec blocked-client --namespace=netpol-lab -- curl --max-time 5 http://web
```

The names and labels did not enforce anything by themselves. This demonstrated the default pod-network behavior: reachable workloads may generally communicate until policy isolates them.

---

## 5. Default-Deny Ingress

The first policy selected the `web` pod and defined no permitted ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-web
  namespace: netpol-lab
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
    - Ingress
```

After applying it, curl from both clients timed out. The policy was stored in the Kubernetes control plane and enforced by Calico; it was not inserted into or understood by the Nginx container.

---

## 6. Label-Based Allow Rule

The second policy selected the same destination but allowed TCP/80 only from pods labeled `access=allowed`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-labeled-client
  namespace: netpol-lab
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              access: allowed
      ports:
        - protocol: TCP
          port: 80
```

Observed result:

| Source | Result |
|---|---|
| `allowed-client` (`access=allowed`) | Nginx page returned |
| `blocked-client` (`access=blocked`) | Timed out |

Standard Kubernetes NetworkPolicies do not have ordered firewall rules or an explicit deny action. Once a pod is isolated, every applicable policy contributes to the union of allowed traffic. If any applicable policy permits a connection, it is allowed. CNI-specific extensions such as Calico policy can provide richer deny and precedence semantics, but those were outside this exercise.

---

## 7. Root Container Baseline

The Nginx container's identity was inspected:

```powershell
kubectl exec web --namespace=netpol-lab -- id
```

Observed:

```text
uid=0(root) gid=0(root)
```

Container root is normally separated from node root by Linux namespaces, capabilities, seccomp, the container runtime, and other boundaries. It does not automatically permit node escape. It does give an attacker more power inside the container and can make dangerous mounts, excessive capabilities, device exposure, or kernel/runtime vulnerabilities easier to exploit.

---

## 8. Hardened Pod

A separate BusyBox pod was created to test restrictions without altering the Nginx workload:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
  namespace: netpol-lab
spec:
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: hardened
      image: busybox:1.36.1
      command: ["sleep", "86400"]
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
```

The YAML was a Pod manifest because `kind: Pod` told Kubernetes which object to create. `metadata.name: hardened-pod` determined the object name; the filename did not. This did not duplicate, modify, or apply a policy to `web`.

### Verified controls

1. `id` returned UID and GID `1000`, proving non-root execution.
2. Creating `/test-file` failed with `Read-only file system`.
3. `/var/run/secrets/kubernetes.io/serviceaccount` did not exist, proving that no ServiceAccount token was mounted.
4. `/proc/1/status` showed:

```text
CapEff:       0000000000000000
NoNewPrivs:   1
Seccomp:      2
```

These values proved that the process had no effective Linux capabilities, could not gain new privileges through execution, and was running with seccomp filtering enabled.

Non-root permissions and a read-only root filesystem are independent controls. A non-root user is constrained by normal Unix ownership and mode bits; `readOnlyRootFilesystem: true` additionally makes the filesystem mount read-only. A workload may still use explicitly mounted writable volumes when required.

---

## 9. Questions and Answers

### Is a curl container only useful for curl?

In this lab its only role was to generate test traffic. Curl containers are commonly used to troubleshoot internal APIs, DNS, TLS, headers, authentication, and response codes. A production application normally uses its language's HTTP library.

### Did `sleep 86400` keep the pod running?

Yes. A container remains running while its main process is running. After 86,400 seconds, `sleep` exits and a non-restarting test pod becomes `Completed`.

### Was `http://web` assigned to the server?

Yes. The Service named `web` created a stable virtual endpoint and Kubernetes DNS name and forwarded TCP/80 traffic to the matching Nginx pod.

### Is NetworkPolicy inserted into the container?

No. Kubernetes stores the object in the control plane and Calico enforces it in the networking layer. The application container remains unchanged.

### Is default-deny followed by an allowlist like firewall ordering?

The outcome resembles default-deny plus allowlisting, but standard NetworkPolicy has no ordered first-match evaluation. Allowed traffic is the union of all applicable allow rules.

### What wins if policies conflict?

Standard NetworkPolicy has no explicit deny that can conflict with an allow. If any applicable policy allows the connection, it is allowed. Traffic not included in the combined allowed set remains blocked for an isolated direction.

### Does container root automatically allow escape?

No. Root inside a container is not automatically root on the node. Escape still requires another weakness or dangerous configuration, but container root usually gives an attacker more options and makes the path easier.

### Did the hardening YAML modify the web pod?

No. `kind: Pod` and `metadata.name: hardened-pod` created a separate BusyBox pod. NetworkPolicy and `securityContext` solve different problems: the first controls traffic, while the second limits Linux process privileges.

---

## 10. Security Model Demonstrated

```text
NetworkPolicy limits who can reach the workload
                    +
securityContext limits what the workload can do
                    +
token automount disabled limits available credentials
```

These are defense-in-depth controls. None assumes that the application itself will remain uncompromised.

---

## 11. Cleanup

The namespace was deleted, removing its four pods, Service, and both NetworkPolicies:

```powershell
kubectl delete namespace netpol-lab
```

The separate Calico-enabled cluster was then removed:

```powershell
minikube delete --profile netpol-lab
```

Finally, `kubectl` was returned to the original `minikube` context. The original cluster and its pre-existing workloads were preserved.

---

## 12. Key Takeaways

- Kubernetes networking is generally open between reachable pods until NetworkPolicy isolates traffic.
- A NetworkPolicy object requires a CNI that actually enforces it.
- Services provide stable internal addressing and DNS independently of pod lifetimes.
- Standard NetworkPolicy is additive and allow-based, not an ordered allow/deny firewall language.
- Container root is not automatically node root, but avoiding it reduces post-compromise power.
- Non-root execution, dropped capabilities, no-new-privileges, read-only filesystems, seccomp, and credential minimization address different parts of the attack surface.
- Security settings should be verified from the running workload rather than assumed from YAML alone.
