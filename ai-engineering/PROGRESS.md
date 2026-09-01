# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 1, 2026  
**Primary direction:** Applied / Agentic AI Engineering with a security focus  
**Scale:** 0–10, where 10 represents strong specialist-level working knowledge  
**Scoring policy:** Scores change only when a dated lab contains demonstrated implementation evidence. Discussion, recognition, architecture ideas, or correct conceptual answers alone do not increase a score.

---

## Target Outcome

Build reliable AI systems around existing foundation models rather than focus primarily on model training.

```text
External event / alert
        ↓
Deterministic API + schema validation
        ↓
Agent state
        ↓
LLM decision
        ↓
Structured tool request
        ↓
Deterministic authorization / policy gate
        ↓
Tool execution
        ↓
Observation returned to agent
        ↓
Evaluate / retry / escalate / finish
```

The long-term target is a security investigation agent that can collect evidence, select approved tools, reason over results, verify its output against explicit criteria, and request human approval before high-risk actions.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Evidence status |
|---|---:|---:|---:|---:|---|
| LLM API Fundamentals | 2.0 | 2.0 | 8.0 | — | No direct LLM API lab yet |
| Structured Outputs / Schemas | 2.0 | 2.25 | 8.0 | +0.25 | Implemented typed Pydantic input schema and constraint validation; LLM output schema still pending |
| Tool / Function Calling | 2.0 | 2.0 | 8.0 | — | Concept only |
| Agent Orchestration | 2.5 | 2.5 | 8.0 | — | Concept only |
| State Machines / Workflow Control | 2.5 | 2.5 | 8.0 | — | Concept only |
| Deterministic Gates / Policy Controls | 3.0 | 3.25 | 8.0 | +0.25 | Demonstrated deterministic rejection of malformed external input before handler execution |
| Evaluation / Rubrics | 2.0 | 2.0 | 8.0 | — | No evaluation harness yet |
| Self-Correction / Bounded Retry | 2.0 | 2.0 | 7.5 | — | Discussed only; retry loop not implemented |
| RAG / Retrieval | 1.5 | 1.5 | 7.5 | — | Not implemented |
| Agent Memory / Persistent State | 1.5 | 1.5 | 7.5 | — | Not implemented |
| Agent Security / Threat Modeling | 3.5 | 3.5 | 8.5 | — | Security foundation exists; no AI-specific attack lab yet |
| AI Application Deployment | 3.0 | 3.5 | 7.5 | +0.5 | Built and ran the alert API in Docker; no LLM service deployment yet |
| AI Observability / Tracing / Cost | 1.5 | 1.5 | 7.5 | — | Not implemented |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg)

The solid filled polygon is **current demonstrated progress**. The dashed outline is the target level. Topic labels and current scores are placed around the outer wheel.

---

## Evidence History

### September 1, 2026 — Baseline

The initial scores were deliberately conservative. Existing security, cloud, Kubernetes, API, identity, permissions, and trust-boundary experience provides useful transfer, but conceptual discussion of agents does not count as hands-on AI implementation.

Topics already discussed before hands-on work included:

- Agent orchestration.
- Nondeterministic LLM decisions versus deterministic code.
- Approval and authorization gates.
- State machines.
- Rubrics and evaluators.
- Self-correcting / self-healing behavior.
- Bounded retry loops.
- Tool calling.
- RAG and memory.
- Containerized FastAPI alert ingestion.

**Score changes:** None. This was the baseline.

---

### September 1, 2026 — Lab 1: FastAPI JSON Alert Receiver

**Evidence:** [AI Engineering Lab 1 — FastAPI JSON Alert Receiver](2026-09-01-lab-01-fastapi-json-alert-receiver.md)

Demonstrated hands-on:

- Created and activated a Python virtual environment.
- Installed and ran FastAPI and Uvicorn.
- Created GET and POST API endpoints.
- Used FastAPI-generated `/docs` and OpenAPI behavior.
- Defined a Pydantic `Alert` model.
- Demonstrated that model fields without defaults are required.
- Rejected a missing required field before the handler ran.
- Restricted severity with `Literal["low", "medium", "high", "critical"]`.
- Rejected an invalid severity value.
- Validated IPv4/IPv6 syntax with `IPvAnyAddress`.
- Validated timestamp structure with `datetime`.
- Distinguished FastAPI, Uvicorn, ASGI, `main.py`, and the in-memory `app` object.
- Built the service into a Docker image.
- Diagnosed a Windows `Dockerfile.txt` naming failure.
- Ran the API entirely from the Docker container with the host Uvicorn process stopped.
- Verified `POST /alert` still worked from the containerized service.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Structured Outputs / Schemas | 2.0 | 2.25 | Practical schema/type/constraint validation was demonstrated, but not yet on LLM output |
| Deterministic Gates / Policy Controls | 3.0 | 3.25 | Demonstrated deterministic input rejection before downstream application logic |
| AI Application Deployment | 3.0 | 3.5 | Built and ran a reproducible containerized service that will become the agent boundary |

**Why the increases are limited:** The lab was guided, contained no actual LLM call, and did not yet implement authorization gates around model-selected actions. LLM API, orchestration, tool calling, evaluation, and retry scores therefore remain unchanged.

---

# Hands-On Lab Roadmap

| Lab | Topic | Core outcome | Status |
|---:|---|---|---|
| 1 | JSON Alert Receiver | FastAPI + Pydantic + Docker deterministic boundary | **Completed** |
| 2 | Structured LLM Alert Triage | Direct LLM API call with validated structured result | Next |
| 3 | Read-Only Investigation Tools | Model selects tools; Python executes validated calls | Planned |
| 4 | Policy-Gated Tools | Separate model intent from deterministic authorization | Planned |
| 5 | Investigation State Machine | Explicit states, transitions, limits, and terminal outcomes | Planned |
| 6 | Rubrics and Evaluation | Repeatable test cases and failure categories | Planned |
| 7 | Bounded Self-Correction | Evaluate → feedback → limited retry → escalate | Planned |
| 8 | RAG | Retrieve security knowledge with source attribution | Planned |
| 9 | Persistent State / Memory | Resume investigations from external state | Planned |
| 10 | Agent Security | Prompt injection, malicious tool output, exfiltration, permission attacks | Planned |
| 11 | Observability | Trace model calls, tools, states, policy decisions, latency, tokens, and cost | Planned |
| 12 | Cloud / Kubernetes Deployment | Apply workload identity, least privilege, secrets, network and pod controls | Planned |

---

## Lab 2 Target Architecture

```text
validated Alert object
        ↓
LLM API
        ↓
structured triage result
        ↓
Pydantic validation
        ↓
application accepts / rejects result
```

Example target result:

```json
{
  "classification": "credential_abuse",
  "severity": "high",
  "needs_investigation": true,
  "confidence": 0.87
}
```

Lab 2 should demonstrate a direct model API call, structured output, deterministic parsing/validation, handling of invalid or refused output, and observation of latency/token usage. It should still avoid a full agent framework so the control boundary remains visible.

---

## Learning Order

```text
1. API + JSON validation              DONE
2. LLM API                            NEXT
3. structured LLM outputs
4. tool calling
5. deterministic policy gates
6. state machine
7. evaluation/rubric
8. bounded self-correction
9. RAG
10. memory/state persistence
11. agent security
12. observability
13. AWS/Kubernetes deployment
```

Do not rely heavily on agent frameworks at the beginning. Implement the first versions directly enough to understand model calls, schema validation, state, tool execution, retry behavior, and security boundaries before adding orchestration frameworks.

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
9. Score changes, only when justified.

A correct conceptual answer alone does not raise a score.