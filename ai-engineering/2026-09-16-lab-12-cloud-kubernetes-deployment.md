# Lab 12 — Cloud / Kubernetes Deployment

**Date:** September 16, 2026  
**Status:** Completed — local first pass  
**Scope:** Docker + Minikube/Kubernetes deployment, runtime secrets, Service routing, scaling, self-healing, resource controls, container hardening, and failure testing. AWS/EKS deployment was intentionally deferred.

---

## Goal

Move a small AI-backed FastAPI service from a directly run Python process into a containerized Kubernetes workload and validate the main deployment/security boundaries.

Target architecture for this lab:

```text
client
  ↓
Kubernetes Service
  ↓
Deployment-managed Pod(s)
  ↓
FastAPI container
  ↓
OPENAI_API_KEY injected from Kubernetes Secret
  ↓
OpenAI API
```

The lab focused on understanding exactly which layer owns the image, running container, Pod, Service, Secret, scaling, and desired-state reconciliation.

---

## 1. Deployable FastAPI Service

Created `deployment_app.py` with two endpoints:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI()


class TriageRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triage")
def triage(request: TriageRequest):
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=request.message
    )

    return {
        "result": response.output_text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens
    }
```

Validated `/health` locally before containerization.

### Important distinction

A top-to-bottom Python script that exits is not a long-running service workload. FastAPI/Uvicorn provides a process that listens continuously on a port and is therefore suitable for a Kubernetes Service/Deployment model.

---

## 2. Docker Image

Initial Dockerfile:

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY deployment_app.py .
RUN pip install --no-cache-dir fastapi uvicorn openai pydantic
EXPOSE 8000
CMD ["uvicorn", "deployment_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Built and tested locally:

```powershell
docker build -t ai-deployment-lab .
docker run --rm -p 8000:8000 -e OPENAI_API_KEY=$env:OPENAI_API_KEY ai-deployment-lab
```

### Troubleshooting: Docker CLI vs Docker engine

Initial Docker commands failed with:

```text
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

`docker version` showed the client but no Server section. Starting Docker Desktop restored the Linux engine and the image built successfully.

### Key lesson

```text
Docker image     = packaged application template
Docker container = running instance created from an image
Kubernetes       = orchestration layer managing Pods/containers
```

The user already understood Kubernetes as an orchestration system at a high level; the lab exposed a narrower hands-on fluency gap around image stores, containers, Pods, and the exact command boundaries.

---

## 3. Kubernetes Contexts and Minikube

`kubectl get nodes` initially tried to reach an old GKE cluster and failed because a GKE authentication plugin was blocked by Windows Application Control.

`kubectl config get-contexts` showed:

```text
gke_cicd-sec-lab_us-central1_sec-lab-cluster
minikube
```

Switched contexts:

```powershell
kubectl config use-context minikube
kubectl config current-context
kubectl get nodes
```

Result:

```text
minikube   Ready   control-plane
```

### Q: Is a Kubernetes context like `git checkout`?

Roughly yes. A context is a saved connection profile telling `kubectl` which cluster/user/namespace to use. Switching contexts is analogous to selecting which target future commands operate against, though a context may point to an entirely different cluster rather than another branch of one repository.

---

## 4. Docker Image Store vs Minikube Image Store

The image built in Docker Desktop did not initially appear in:

```powershell
minikube image ls
```

because Docker Desktop and Minikube can have separate image stores.

Loaded the existing image into Minikube:

```powershell
minikube image load ai-deployment-lab
minikube image ls | Select-String ai-deployment-lab
```

PowerShell note: `Select-String` is PowerShell-specific. The equivalent filter in `cmd.exe` is `findstr`.

### Q: Does `minikube image ls` show a running Kubernetes container?

No. Both `docker image ls` and `minikube image ls` list stored images. A container is only created later when Docker or Kubernetes starts a workload from the image.

---

## 5. Kubernetes Secret

Created a Kubernetes Secret from the local shell value:

```powershell
kubectl create secret generic openai-api-key `
  --from-literal=OPENAI_API_KEY="$env:OPENAI_API_KEY"
```

The Deployment injects it into the running container:

```yaml
env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: openai-api-key
        key: OPENAI_API_KEY
```

### Q: Is the image accessing the API key?

No. The stored image has no OpenAI key. Kubernetes creates a running Pod/container from the image and injects `OPENAI_API_KEY` into that container's runtime environment.

### Q: Can a container attacker see the OpenAI key?

If an attacker gains code execution with the same effective permissions as the application, the key is generally accessible because the application itself must be able to read it. A mounted Secret file can reduce accidental environment exposure but does not create a strong boundary against full application/container compromise.

### Production extension

A production cloud environment would more commonly use an external secret manager plus workload identity. That was discussed but intentionally not implemented because AWS access/setup was deferred.

---

## 6. Deployment and Service

Created a Deployment using the locally loaded image, initially with one replica:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-deployment
  template:
    metadata:
      labels:
        app: ai-deployment
    spec:
      containers:
        - name: ai-deployment
          image: ai-deployment-lab
          imagePullPolicy: Never
          ports:
            - containerPort: 8000
```

`imagePullPolicy: Never` was used because the image was loaded directly into Minikube rather than published to a registry.

Added readiness and liveness checks against `/health`.

Created a ClusterIP Service in the same YAML file, separated by the meaningful YAML document separator `---`:

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: ai-deployment-service
spec:
  selector:
    app: ai-deployment
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

Applied desired state:

```powershell
kubectl apply -f deployment.yaml
```

Observed:

```text
deployment.apps/ai-deployment unchanged
service/ai-deployment-service created
```

This demonstrated Kubernetes reconciliation: existing resources already matching desired state were unchanged; missing desired resources were created.

---

## 7. Service Routing and Real AI Request

Forwarded local port 8080 to the Kubernetes Service:

```powershell
kubectl port-forward service/ai-deployment-service 8080:80
```

Validated:

```text
http://127.0.0.1:8080/health
→ {"status":"ok"}
```

Then sent a real `/triage` request and received a valid OpenAI-generated response with input/output token counts. This proved the full runtime path:

```text
client
→ Service
→ Pod
→ FastAPI
→ Kubernetes Secret injected as OPENAI_API_KEY
→ OpenAI API
→ response
```

PowerShell/curl JSON quoting caused an intermediate `json_invalid` failure. Using PowerShell-native `Invoke-RestMethod` avoided the quoting issue.

---

## 8. Self-Healing and Desired State

Deleted a running Pod manually:

```powershell
kubectl delete pod <pod-name>
```

The Deployment automatically created a replacement because desired state remained:

```yaml
replicas: 1
```

Mental model:

```text
desired = 1 Pod
actual  = 0 Pods
        ↓
Kubernetes reconciles
        ↓
replacement Pod created
```

This was the clearest hands-on demonstration of the difference between directly running a container and declaring desired state to an orchestrator.

---

## 9. Scaling and Service Discovery

Changed:

```yaml
replicas: 1
```

to:

```yaml
replicas: 3
```

Kubernetes created two additional Pods.

Checked the Service EndpointSlice and observed three Pod IPs. The Service discovered all matching Pods automatically through:

```yaml
selector:
  app: ai-deployment
```

### Q: Why did scaling 1 → 3 not change the Pod hash?

Because `spec.replicas` changes quantity only. It does not alter `spec.template`, so Kubernetes continues using the same ReplicaSet/Pod template hash.

---

## 10. Resource Requests and Limits

Added:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

Interpretation:

- `requests` influence scheduling/reservation;
- `limits` cap container resource use;
- `100m` CPU = 0.1 CPU;
- `500m` CPU = 0.5 CPU.

Because this changed `spec.template`, Kubernetes generated a new ReplicaSet hash and performed a rolling update.

### Q: When does the Deployment hash change?

Changes to the Pod template—image, environment, resources, probes, template labels, security context, etc.—create a new ReplicaSet hash. Changing only replica count does not.

---

## 11. Non-Root Container and Kubernetes Security Context

Created a new image version:

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY deployment_app.py .
RUN pip install --no-cache-dir fastapi uvicorn openai pydantic
RUN useradd --create-home --uid 10001 appuser
USER 10001
EXPOSE 8000
CMD ["uvicorn", "deployment_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Built and loaded:

```powershell
docker build -t ai-deployment-lab:v2 .
minikube image load ai-deployment-lab:v2
```

Updated the Deployment image to `ai-deployment-lab:v2` and added:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

Verified the actual runtime identity:

```text
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

### Layer distinction

```text
Dockerfile USER 10001
→ image is designed to run non-root

Kubernetes securityContext
→ cluster/runtime explicitly enforces the intended privilege boundary
```

---

## 12. Disable Automatic ServiceAccount Token Mounting

Added at Pod level:

```yaml
automountServiceAccountToken: false
```

This prevents Kubernetes from automatically placing the Pod's ServiceAccount token into the container.

### Q: Does this protect `OPENAI_API_KEY`?

No. It reduces Kubernetes-cluster blast radius by removing an unnecessary Kubernetes credential. The OpenAI key is separately injected from the Kubernetes Secret and remains available to the application process.

The app does not need to call the Kubernetes API, so withholding that credential follows least privilege.

---

## 13. Failure Testing

### Failure 1 — Secret object deleted

Deleted:

```powershell
kubectl delete secret openai-api-key
```

Then forced a new Pod. The new Pod showed:

```text
CreateContainerConfigError
```

Reason: Kubernetes could create the Pod object, but could not configure/start the container because the referenced Secret did not exist.

### Failure 2 — Secret exists but value is unusable

The Secret was recreated from a PowerShell session where `OPENAI_API_KEY` was not populated correctly. The Pod progressed beyond configuration but the application crashed:

```text
Running
→ Error
→ Running
→ Error
→ CrashLoopBackOff
```

`kubectl logs <pod> --previous` showed:

```text
openai.OpenAIError: Missing credentials...
```

This produced an important operational distinction:

```text
Secret object missing
→ CreateContainerConfigError
→ failure before container/application startup

Secret object exists, bad/empty value
→ container starts
→ application fails
→ CrashLoopBackOff
```

The Deployment continued retrying because desired state still required the workload to be running.

---

## Questions and Answers Summary

### Is Minikube just Docker with different commands?

No. Minikube runs a local Kubernetes cluster. `minikube` mainly manages that cluster and its local image environment; `kubectl` manages Kubernetes workloads. Docker directly builds/runs containers, while Kubernetes orchestrates Pods/containers through declarative resources.

### Is the high-level idea Docker = one instance and Kubernetes = orchestration?

Yes. Docker provides the image/container layer. Kubernetes adds desired-state management, replicas, self-healing, rolling updates, Services, Secrets, resource controls, and workload security configuration.

### Was this Kubernetes knowledge expected before the lab?

At a high level, yes: container, Pod, Deployment, Service, orchestration. The lab showed that the high-level architecture was already understood but the command-level/runtime boundaries needed reinforcement.

### What does `---` mean in `deployment.yaml`?

It is a real YAML document separator. It allows one YAML file to contain multiple Kubernetes objects, such as a Deployment and a Service.

### Can there only be one `deployment.yaml`?

No. The filename is conventional only. Kubernetes cares about the resource definitions and names inside the files.

### What is Kubernetes desired state?

The YAML declares what should exist. Kubernetes continuously compares desired state with actual cluster state and reconciles differences.

### Why did Pods get new names after resource/security changes?

Those changes modified `spec.template`, causing a new ReplicaSet/template hash and a rolling rollout. Scaling only `replicas` reused the same template/hash.

### Does mounting a Secret instead of using an environment variable fully protect it?

No. It can reduce accidental environment exposure and has different update semantics, but if an attacker controls the application/container and the application can read the secret, the attacker can generally read it too.

---

## Security Implications

Controls exercised in this lab:

- runtime Secret injection instead of baking API keys into the image;
- non-root container user;
- Kubernetes `runAsNonRoot` and fixed UID;
- privilege escalation disabled;
- Linux capabilities dropped;
- resource requests/limits;
- readiness/liveness probes;
- no unnecessary ServiceAccount token;
- stable Service abstraction instead of addressing disposable Pods directly;
- explicit failure-path testing for missing and unusable secrets.

Important remaining limitations:

- Kubernetes Secret stored locally in Minikube; no external secret manager;
- no EKS/ECR or other managed cluster/registry;
- no workload identity;
- no NetworkPolicy/egress allowlisting;
- no ingress/TLS/load balancer;
- no Pod Security Admission exercise in this lab;
- no image scanning/signing/admission policy;
- no centralized logging/metrics backend;
- no autoscaling;
- no CI/CD deployment pipeline;
- no persistent database integration with the deployed app;
- deployment service was intentionally minimal rather than the entire Labs 1–11 agent stack.

---

## Independent Understanding vs Guidance

The implementation was heavily guided, so this does not demonstrate independent production Kubernetes design yet.

However, the user independently reasoned correctly about several architecture points during the lab:

- Kubernetes as desired-state orchestration rather than direct container management;
- scaling replica count vs changing the Pod template;
- the difference between a runtime Secret and an image;
- the fact that a compromised application can generally access a credential the application itself needs;
- `automountServiceAccountToken: false` reducing cluster credential exposure rather than protecting the OpenAI key;
- the high-level Docker/container/Kubernetes separation.

The clearest gap exposed was operational fluency: contexts, separate image stores, Service/EndpointSlice behavior, Secret injection, ReplicaSet hashes, and specific `kubectl`/Minikube command behavior.

---

## Score Change

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| AI Application Deployment | 3.5 | 4.5 | Hands-on containerization and Minikube deployment; Service routing; Secret injection; probes; self-healing; scaling; resource constraints; non-root/security-context enforcement; ServiceAccount-token reduction; and real failure-path troubleshooting |

### Why the increase is limited

The lab was guided and local. It did not demonstrate independent deployment design, cloud Kubernetes provisioning, workload identity, external secret management, registry integration, production ingress/network policy, autoscaling, or deployment automation.

No other AI score changes are justified: the lab deployed a minimal AI API and exercised deployment/runtime security rather than adding new LLM, tool-calling, orchestration, RAG, memory, evaluation, or observability capabilities.

---

## First-Pass Roadmap Status

Labs 1–12 are now complete.

The next phase should be a more independent second pass that integrates more of the earlier agent components into one service and requires substantially less implementation scaffolding.