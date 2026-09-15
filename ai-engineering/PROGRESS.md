# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 14, 2026  
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
```

The long-term target is a security-focused AI application that can retrieve trusted knowledge, preserve workflow state across restart, collect evidence, choose approved tools, reason over results, verify outputs against explicit criteria, use bounded correction when appropriate, require deterministic policy/approval before high-risk actions, and make model/tool/workflow behavior observable.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Evidence status |
|---|---:|---:|---:|---:|---|
| LLM API Fundamentals | 2.0 | 3.0 | 8.0 | +1.0 | Responses API, structured parsing, function-call continuation, environment-key handling, FastAPI integration, API-error handling |
| Structured Outputs / Schemas | 2.0 | 3.5 | 8.0 | +1.5 | Pydantic API/LLM schemas, JSON Schema tool definitions, execution-time validation |
| Tool / Function Calling | 2.0 | 3.75 | 8.0 | +1.75 | Read-only and state-changing tools, model-selected calls, dynamic dispatch, result return, approval-gated actions |
| Agent Orchestration | 2.5 | 3.0 | 8.0 | +0.5 | Guided model/tool workflow with shared investigation state; general multi-action/tool-loop limitation remains |
| State Machines / Workflow Control | 2.5 | 3.5 | 8.0 | +1.0 | Explicit FSM states, legal transitions, deterministic enforcement, terminal outcomes |
| Deterministic Gates / Policy Controls | 3.0 | 5.25 | 8.0 | +2.25 | Input/review gates, tool allowlist, argument/policy validation, approval, deterministic state transitions, pre-model secret redaction |
| Evaluation / Rubrics | 2.0 | 3.0 | 8.0 | +1.0 | Repeatable eval harness, ground-truth state/tool expectations, PASS/FAIL summary, intentional regression test |
| Self-Correction / Bounded Retry | 2.0 | 3.0 | 7.5 | +1.0 | Fixed retry budget, evaluator feedback, real LLM correction, deterministic hard-stop behavior |
| RAG / Retrieval | 1.5 | 3.0 | 7.5 | +1.5 | End-to-end RAG with embeddings, cosine similarity, top-k, thresholding, source IDs, stored doc embeddings, grounding tests |
| Agent Memory / Persistent State | 1.5 | 3.0 | 7.5 | +1.5 | SQLite-backed investigation state and pending actions, restart recovery, FSM reconstruction, persistent approve/reject and success/failure outcomes |
| Agent Security / Threat Modeling | 3.5 | 5.25 | 8.5 | +1.75 | Indirect prompt injection, poisoned tool output, authorization/approval boundaries, capability allowlisting, exfiltration controls, model-vs-system compromise analysis |
| AI Application Deployment | 3.0 | 3.5 | 7.5 | +0.5 | Lab 1 Docker deployment; newer LLM/tool/FSM/eval/retry/RAG/persistence/security/observability code not yet redeployed in container/cloud |
| AI Observability / Tracing / Cost | 1.5 | 3.0 | 7.5 | +1.5 | Request correlation, model latency/tokens/cost, tool/policy/state events, JSONL traces, request summaries, aggregate metrics/rates, threshold alerts |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg?v=20260914-lab11)

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

Built a local correlated telemetry pipeline around an LLM/agent workflow:

- measured model-call latency with `time.perf_counter()`;
- captured model name, input/output/total tokens, output, and approximate API cost;
- generated a UUID `request_id` and used it across model, tool, policy, execution, and state events;
- logged model tool intent separately from deterministic policy decisions and actual execution;
- dynamically recorded `allow`, `block`, and `require_approval` policy outcomes;
- simulated success and failure tool paths and logged `success` vs `error` execution status;
- connected execution/policy outcome to simplified workflow state (`completed`, `blocked`, `awaiting_approval`);
- serialized events to JSON and appended one event per line to `agent_trace.jsonl`;
- reconstructed chronological traces by `request_id`;
- reduced event streams into per-request summaries;
- debugged a duplicate `model_call` schema that caused `KeyError: estimated_cost_usd`;
- fixed a stale tool-name trace inconsistency and a policy-order bug where a high-risk tool was not also authorized;
- aggregated traces into request count, average latency, tokens, cost, execution errors, final-state counts, and rates;
- added threshold-based alerts for high execution-error and blocked-request rates;
- identified that test-heavy traffic can distort operational metrics.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| AI Observability / Tracing / Cost | 1.5 | 3.0 | Implemented correlated model/tool/policy/state telemetry, JSONL persistence, latency/token/cost tracking, trace reconstruction, request summaries, aggregate metrics/rates, and threshold alerts |

**Why other scores did not increase:** The lab reused the existing tool, policy, and state concepts. The new evidence is primarily instrumentation and analysis, not deeper orchestration or policy implementation.

**Important design lessons:** observability must distinguish model intent, policy authorization, execution outcome, and workflow state; logs themselves need consistent schemas and correct runtime values; and aggregate metrics only have meaning when the traffic population is understood.

**Limitations:** local JSONL only; no OpenTelemetry/LangSmith/CloudWatch/OpenSearch backend, no distributed spans, dashboards, percentile latency, production retention, schema versioning, real FSM instrumentation, or baseline-derived alert thresholds.

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
| 12 | Cloud / Kubernetes Deployment | Workload identity, least privilege, secrets, network/pod controls | **Next** |

---

## Lab 12 Target Architecture

```text
containerized AI application
        ↓
cloud / Kubernetes workload identity
        ↓
least-privilege access to secrets + cloud services
        ↓
network / pod / runtime controls
        ↓
model API + tools + persistence
        ↓
centralized logs / traces / metrics
```

Lab 12 should move the application from local-only code toward a realistic deployment boundary while preserving the security, persistence, and observability controls built in earlier labs.

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
13. AWS/Kubernetes deployment         NEXT
```

Do not rely heavily on agent frameworks at the beginning. Implement the first versions directly enough to understand model calls, validation, state, tool execution, retry behavior, retrieval, persistence, security boundaries, and observability before adding orchestration frameworks.

---

## Evidence Rules for Future Updates

After each lab, create a dated Markdown note under `ai-engineering/` containing:

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