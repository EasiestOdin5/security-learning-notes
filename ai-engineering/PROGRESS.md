# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 18, 2026  
**Primary direction:** Applied / Agentic AI Engineering with a security focus  
**Scale:** 0–10, where 10 represents strong specialist-level working knowledge  
**Scoring policy:** Scores change only when dated labs contain demonstrated implementation evidence. Discussion or recognition alone does not raise a score.

---

## Target Outcome

Build reliable AI systems around existing foundation models rather than focus on model training.

```text
External event / question
        ↓
Deterministic API + schema validation
        ↓
Durable agent state / retrieval context
        ↓
LLM decision or grounded answer
        ↓
Structured tool request / recommendation
        ↓
Deterministic authorization / policy gate
        ↓
Tool execution
        ↓
Persist outcome / evaluate / bounded retry / escalate / finish
        ↓
Trace / measure / alert
        ↓
Secure deployment boundary
```

The long-term target is a security-focused AI application that can retrieve trusted knowledge, preserve workflow state across restart, collect evidence, choose approved tools, reason over results, verify outputs against explicit criteria, use bounded correction when appropriate, require deterministic policy/approval before high-risk actions, make model/tool/workflow behavior observable, and run behind a defensible deployment boundary.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Evidence status |
|---|---:|---:|---:|---:|---|
| LLM API Fundamentals | 2.0 | 3.0 | 8.0 | +1.0 | Responses API, structured parsing, function-call continuation, environment-key handling, FastAPI integration, API-error handling |
| Structured Outputs / Schemas | 2.0 | 3.75 | 8.0 | +1.75 | Pydantic API/LLM schemas, JSON Schema tool definitions, execution-time validation, Pass 2 independent API-schema reconstruction |
| Tool / Function Calling | 2.0 | 3.75 | 8.0 | +1.75 | Read-only and state-changing tools, model-selected calls, dynamic dispatch, result return, approval-gated actions |
| Agent Orchestration | 2.5 | 3.0 | 8.0 | +0.5 | Guided model/tool workflow with shared investigation state; general multi-action/tool-loop limitation remains |
| State Machines / Workflow Control | 2.5 | 3.5 | 8.0 | +1.0 | Explicit FSM states, legal transitions, deterministic enforcement, terminal outcomes |
| Deterministic Gates / Policy Controls | 3.0 | 5.25 | 8.0 | +2.25 | Input/review gates, tool allowlist, argument/policy validation, approval, deterministic state transitions, pre-model secret redaction |
| Evaluation / Rubrics | 2.0 | 3.0 | 8.0 | +1.0 | Repeatable eval harness, ground-truth state/tool expectations, PASS/FAIL summary, intentional regression test |
| Self-Correction / Bounded Retry | 2.0 | 3.0 | 7.5 | +1.0 | Fixed retry budget, evaluator feedback, real LLM correction, deterministic hard-stop behavior |
| RAG / Retrieval | 1.5 | 3.0 | 7.5 | +1.5 | End-to-end RAG with embeddings, cosine similarity, top-k, thresholding, source IDs, stored doc embeddings, grounding tests |
| Agent Memory / Persistent State | 1.5 | 3.0 | 7.5 | +1.5 | SQLite-backed investigation state and pending actions, restart recovery, FSM reconstruction, persistent approve/reject and success/failure outcomes |
| Agent Security / Threat Modeling | 3.5 | 5.25 | 8.5 | +1.75 | Indirect prompt injection, poisoned tool output, authorization/approval boundaries, capability allowlisting, exfiltration controls, model-vs-system compromise analysis |
| AI Application Deployment | 3.0 | 4.75 | 7.5 | +1.75 | Docker/FastAPI deployment, Minikube Deployment/Service, Secrets, probes, self-healing, scaling, resource controls, non-root runtime, ServiceAccount-token reduction, failure testing, Pass 2 independent Docker reconstruction |
| AI Observability / Tracing / Cost | 1.5 | 3.0 | 7.5 | +1.5 | Request correlation, model latency/tokens/cost, tool/policy/state events, JSONL traces, request summaries, aggregate metrics/rates, threshold alerts |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg?v=20260918-pass2-lab1)

The solid polygon is **current demonstrated progress**. The dashed outline is the target.

---

## Evidence History

### September 1, 2026 — Baseline

Initial scores were deliberately conservative. Existing security, cloud, Kubernetes, API, identity, permission, and trust-boundary experience transfers well, but conceptual discussion alone does not count as hands-on AI implementation.

---

### September 1, 2026 — Lab 1: FastAPI JSON Alert Receiver

**Evidence:** [Lab 1](2026-09-01-lab-01-fastapi-json-alert-receiver.md)

FastAPI/Uvicorn setup, Pydantic alert validation, API docs, Docker build/run, deterministic rejection.

**Score changes:** Structured Outputs 2.0→2.25; Deterministic Gates 3.0→3.25; Deployment 3.0→3.5.

---

### September 1, 2026 — Lab 2: Structured LLM Alert Triage

**Evidence:** [Lab 2](2026-09-01-lab-02-structured-llm-alert-triage.md)

Direct Responses API use, Pydantic structured output, system/user roles, confidence constraints, API-error handling, prompt-injection testing, deterministic review gates.

**Score changes:** LLM API 2.0→2.75; Structured Outputs 2.25→3.25; Deterministic Gates 3.25→3.75; Agent Security 3.5→4.0.

---

### September 1, 2026 — Lab 3: Read-Only Investigation Tools

**Evidence:** [Lab 3](2026-09-01-lab-03-read-only-investigation-tools.md)

Custom tools, strict schemas, model-selected calls, Python execution, function-call result continuation, dynamic dispatch, allowlisting, Pydantic validation, IP policy validation, insufficient-evidence testing.

**Score changes:** LLM API 2.75→3.0; Structured Outputs 3.25→3.5; Tool Calling 2.0→3.5; Orchestration 2.5→2.75; Deterministic Gates 3.75→4.25; Agent Security 4.0→4.25.

---

### September 2, 2026 — Lab 4: Policy-Gated Tools

**Evidence:** [Lab 4](2026-09-02-lab-04-policy-gated-tools.md)

State-changing `disable_user`, approval metadata, UUID-scoped pending actions, exact-action approval/rejection, deterministic execution. A general multi-turn loop was intentionally removed after exposing repeated-call complexity.

**Score changes:** Tool Calling 3.5→3.75; Deterministic Gates 4.25→4.75; Agent Security 4.25→4.5.

---

### September 2, 2026 — Lab 5: Investigation State Machine

**Evidence:** [Lab 5](2026-09-02-lab-05-investigation-state-machine.md)

Explicit FSM with `Enum`, transition table, legal/illegal enforcement, terminal states, and approval/rejection/execution integration.

**Score changes:** Orchestration 2.75→3.0; State Machines 2.5→3.5; Deterministic Gates 4.75→5.0.

**Limitation:** no-action completion is still simplified rather than driven by an explicit structured `investigation_complete` signal.

---

### September 3, 2026 — Lab 6: Rubrics and Evaluation

**Evidence:** [Lab 6](2026-09-03-lab-06-rubrics-and-evaluation.md)

Created `eval_lab.py`, reusable cases, machine-readable state/tool results, automated PASS/FAIL checks, suite summary, a `3/3` baseline, and an intentional `2/3` regression. The eval also exposed a real FSM policy-block bug that was fixed.

**Score changes:** Evaluation / Rubrics 2.0→3.0.

---

### September 4, 2026 — Lab 7: Bounded Self-Correction

**Evidence:** [Lab 7](2026-09-04-lab-07-bounded-self-correction.md)

Built deterministic `MAX_ATTEMPTS`, evaluator feedback, retry input logging, real LLM correction from verbose output to exact `SAFE`, and a real hard-stop test. Also identified that the current tool workflow does not yet support arbitrary multi-step tool loops after read-only enrichment.

**Score changes:** Self-Correction / Bounded Retry 2.0→3.0.

---

### September 11, 2026 — Lab 8: RAG / Retrieval

**Evidence:** [Lab 8](2026-09-11-lab-08-rag-retrieval.md)

Built semantic retrieval progressively from keyword matching to bag-of-words cosine similarity to OpenAI embeddings. Added top-k retrieval, source IDs, minimum similarity threshold, precomputed document embeddings, and grounding tests including an unsupported-detail refusal.

**Score changes:** RAG / Retrieval 1.5→3.0.

**Important lesson:** semantic similarity is useful but not equivalent to correctness; related but wrong documents can outrank intended sources.

---

### September 12, 2026 — Lab 9: Persistent State / Memory

**Evidence:** [Lab 9](2026-09-12-lab-09-persistent-state-memory.md)

Built a standalone persistence layer around SQLite and connected it back to the existing FSM/approval design. Persisted investigations and pending actions, reconstructed FSM state after restart, retained deterministic transition enforcement, persisted approval/rejection and execution success/failure paths, and identified the limitation that one completed action does not necessarily mean the overall investigation is complete.

**Score changes:** Agent Memory / Persistent State 1.5→3.0.

---

### September 12, 2026 — Lab 10: Agent Security

**Evidence:** [Lab 10](2026-09-12-lab-10-agent-security.md)

Stress-tested agent trust boundaries with indirect prompt injection, poisoned tool output, unauthorized capability attempts, approval gating, and pre-model secret redaction. Distinguished model compromise from system compromise and connected agent testing to black-box AppSec reasoning.

**Score changes:** Agent Security / Threat Modeling 4.5→5.25; Deterministic Gates / Policy Controls 5.0→5.25.

---

### September 14, 2026 — Lab 11: AI Observability / Tracing / Cost

**Evidence:** [Lab 11](2026-09-14-lab-11-observability.md)

Built a local correlated telemetry pipeline around an LLM/agent workflow: model latency/tokens/cost, request IDs, tool intent, policy decisions, execution status, simplified workflow state, JSONL persistence, per-request trace reconstruction, summaries, aggregate metrics/rates, and threshold alerts. Debugging also exposed duplicate-event schema issues, stale runtime values, and policy-order inconsistencies.

**Score changes:** AI Observability / Tracing / Cost 1.5→3.0.

**Limitations:** local JSONL only; no OpenTelemetry/LangSmith/CloudWatch/OpenSearch backend, distributed spans, dashboards, percentile latency, production retention, schema versioning, real FSM instrumentation, or baseline-derived alert thresholds.

---

### September 16, 2026 — Lab 12: Cloud / Kubernetes Deployment

**Evidence:** [Lab 12](2026-09-16-lab-12-cloud-kubernetes-deployment.md)

Moved a minimal AI-backed FastAPI service into a local Kubernetes deployment boundary and exercised the runtime behavior directly:

- built and tested a Docker image, then loaded it into Minikube's separate image store;
- switched `kubectl` from an old GKE context to a healthy local Minikube context;
- stored `OPENAI_API_KEY` in a Kubernetes Secret and injected it only at container runtime;
- created a Deployment with health probes and a ClusterIP Service, then verified a real OpenAI request through Service → Pod → FastAPI;
- demonstrated desired-state reconciliation by deleting a Pod and observing automatic replacement;
- scaled from 1 to 3 replicas and verified three Service endpoints;
- distinguished replica-count changes from Pod-template changes and observed new ReplicaSet hashes during rolling updates;
- added CPU/memory requests and limits;
- rebuilt the image as `v2` with UID 10001 and enforced `runAsNonRoot`, fixed UID, no privilege escalation, and dropped capabilities;
- disabled automatic ServiceAccount token mounting because the application does not call the Kubernetes API;
- tested missing-secret failure (`CreateContainerConfigError`);
- tested an unusable/empty secret value that allowed container startup but caused the application to exit and enter `CrashLoopBackOff`;
- used previous-container logs to identify the OpenAI missing-credentials exception.

The lab also clarified that Docker supplies the image/container layer while Kubernetes supplies orchestration, desired state, scaling, self-healing, Service discovery, runtime configuration, and workload controls.

**Score changes:** AI Application Deployment 3.5→4.5.

**Why the increase is limited:** The implementation was heavily guided and local. No EKS/ECR, workload identity, external secret manager, registry-based rollout, ingress/TLS, NetworkPolicy, autoscaling, CI/CD deployment, image admission/signing, or independent production architecture was demonstrated.

---

### September 18, 2026 — Pass 2 Lab 1: FastAPI JSON Alert Receiver

**Evidence:** [Pass 2 Lab 1](2026-09-18-pass2-lab-01-fastapi-json-alert-receiver.md)

Rebuilt the first lab from a design brief without supplied implementation code. Independently implemented FastAPI endpoints, a Pydantic `Alert` model, `IPvAnyAddress` validation, enum-based severity validation, a non-empty username constraint, valid/invalid request testing, and a Docker build/run path. Several Pass 1 concepts were refreshed through questions, but the implementation itself was reconstructed rather than copied.

**Score changes:** Structured Outputs / Schemas 3.5→3.75; AI Application Deployment 4.5→4.75.

**Why the increases are limited:** architecture and task sequencing were still supplied, and several implementation concepts required reminders. This is evidence of stronger implementation independence, not yet independent system design.

---

## Pass 2 Roadmap

Pass 2 uses the same 12-topic sequence with a different evidence standard: the design goal is provided, but implementation code is not supplied unless specifically needed after an attempt.

| Pass 2 Lab | Topic | Independence target | Status |
|---:|---|---|---|
| 1 | JSON Alert Receiver | Rebuild FastAPI + Pydantic + Docker from design brief | **Completed** |
| 2 | Structured LLM Alert Triage | Rebuild LLM structured-output path from design brief | **Next** |
| 3 | Read-Only Investigation Tools | Rebuild validated tool-calling path | Planned |
| 4 | Policy-Gated Tools | Rebuild deterministic approval boundary | Planned |
| 5 | Investigation State Machine | Rebuild FSM and legal transitions | Planned |
| 6 | Rubrics and Evaluation | Rebuild evaluation harness | Planned |
| 7 | Bounded Self-Correction | Rebuild evaluator-driven bounded retry | Planned |
| 8 | RAG / Retrieval | Rebuild retrieval pipeline | Planned |
| 9 | Persistent State / Memory | Rebuild persistence and recovery | Planned |
| 10 | Agent Security | Rebuild and test agent trust boundaries | Planned |
| 11 | Observability | Rebuild correlated telemetry and metrics | Planned |
| 12 | Kubernetes Deployment | Rebuild deployment/hardening path | Planned |

---

# Hands-On Lab Roadmap

| Lab | Topic | Core outcome | Status |
|---:|---|---|---|
| 1 | JSON Alert Receiver | FastAPI + Pydantic + Docker deterministic boundary | **Completed** |
| 2 | Structured LLM Alert Triage | Validated structured LLM result and deterministic review gates | **Completed** |
| 3 | Read-Only Investigation Tools | Model selects tools; Python executes validated calls | **Completed** |
| 4 | Policy-Gated Tools | Separate model intent from deterministic authorization/human approval | **Completed** |
| 5 | Investigation State Machine | Explicit states, legal transitions, terminal outcomes | **Completed** |
| 6 | Rubrics and Evaluation | Repeatable cases, expected outcomes, regression baseline | **Completed** |
| 7 | Bounded Self-Correction | Evaluate → feedback → limited retry → hard stop | **Completed** |
| 8 | RAG / Retrieval | Semantic retrieval, top-k, threshold, grounded answer, source attribution | **Completed** |
| 9 | Persistent State / Memory | Durable investigation and pending-action state across restart | **Completed** |
| 10 | Agent Security | Prompt injection, poisoned tool output, exfiltration, permission boundaries | **Completed** |
| 11 | Observability | Correlated model/tool/policy/state traces, cost/latency, metrics and alerts | **Completed** |
| 12 | Cloud / Kubernetes Deployment | Containerized service, Kubernetes desired state, Secrets, Service routing, scaling/self-healing, runtime hardening | **Completed** |

---

## First-Pass Roadmap Complete

All 12 guided first-pass labs are complete.

The next phase should be an **advanced/integrated second pass** with less scaffolding. Instead of another sequence of isolated mini-labs, the goal should be to combine the existing pieces into a more coherent application and require more independent design decisions.

Suggested second-pass direction:

```text
FastAPI boundary
    ↓
structured LLM decision
    ↓
retrieval + persistent investigation state
    ↓
validated tool calls
    ↓
policy / approval / FSM
    ↓
bounded evaluation/retry
    ↓
security controls
    ↓
structured observability
    ↓
containerized Kubernetes deployment
```

Key gaps to target next:

- independent multi-step orchestration rather than guided single-path code;
- clearer action-state vs investigation-state separation;
- real multi-tool loops with bounded termination;
- more realistic RAG chunking/vector-store/retrieval evaluation;
- production-style trace/span instrumentation;
- deploy the integrated agent rather than a minimal deployment-only API;
- cloud registry/workload identity/external secret-manager integration when AWS access is ready;
- more independent implementation with fewer supplied code blocks.

---

## Learning Order

```text
1. API + JSON validation              DONE
2. LLM API                            DONE
3. structured LLM outputs             DONE
4. tool calling                       DONE
5. deterministic tool-policy gates    DONE
6. state machine                      DONE
7. evaluation/rubric                  DONE
8. bounded self-correction            DONE
9. RAG                                DONE
10. persistent state / memory         DONE
11. deeper agent security             DONE
12. observability                     DONE
13. local Kubernetes deployment       DONE
14. integrated/advanced second pass   NEXT
```

Do not rely heavily on agent frameworks until the direct implementation boundaries are comfortable. The second pass should increase independence before adding heavier orchestration abstractions.

---

## Evidence Rules for Future Updates

After each lab/project milestone, create a dated Markdown note under `ai-engineering/` containing:

1. Goal and architecture.
2. Commands/code used.
3. What succeeded.
4. What failed.
5. Troubleshooting performed.
6. Questions and answers.
7. Security implications.
8. What was independently understood versus completed with guidance.
9. Score changes only when justified.

A correct conceptual answer alone does not raise a score.