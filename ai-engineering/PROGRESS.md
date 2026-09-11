# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 11, 2026  
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
Agent state / retrieval context
        ↓
LLM decision or grounded answer
        ↓
Structured tool request / recommendation
        ↓
Deterministic authorization / policy gate
        ↓
Tool execution
        ↓
Evaluate / bounded retry / escalate / finish
```

The long-term target is a security-focused AI application that can retrieve trusted knowledge, collect evidence, choose approved tools, reason over results, verify outputs against explicit criteria, use bounded correction when appropriate, and require deterministic policy/approval before high-risk actions.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Evidence status |
|---|---:|---:|---:|---:|---|
| LLM API Fundamentals | 2.0 | 3.0 | 8.0 | +1.0 | Responses API, structured parsing, function-call continuation, environment-key handling, FastAPI integration, API-error handling |
| Structured Outputs / Schemas | 2.0 | 3.5 | 8.0 | +1.5 | Pydantic API/LLM schemas, JSON Schema tool definitions, execution-time validation |
| Tool / Function Calling | 2.0 | 3.75 | 8.0 | +1.75 | Read-only and state-changing tools, model-selected calls, dynamic dispatch, result return, approval-gated actions |
| Agent Orchestration | 2.5 | 3.0 | 8.0 | +0.5 | Guided model/tool workflow with shared investigation state; multi-step tool-loop limitation remains |
| State Machines / Workflow Control | 2.5 | 3.5 | 8.0 | +1.0 | Explicit FSM states, legal transitions, deterministic enforcement, terminal outcomes |
| Deterministic Gates / Policy Controls | 3.0 | 5.0 | 8.0 | +2.0 | Input/review gates, tool allowlist, argument/policy validation, approval, deterministic state transitions |
| Evaluation / Rubrics | 2.0 | 3.0 | 8.0 | +1.0 | Repeatable eval harness, ground-truth state/tool expectations, PASS/FAIL summary, intentional regression test |
| Self-Correction / Bounded Retry | 2.0 | 3.0 | 7.5 | +1.0 | Fixed retry budget, evaluator feedback, real LLM correction, deterministic hard-stop behavior |
| RAG / Retrieval | 1.5 | 3.0 | 7.5 | +1.5 | End-to-end RAG with embeddings, cosine similarity, top-k, thresholding, source IDs, stored doc embeddings, grounding tests |
| Agent Memory / Persistent State | 1.5 | 1.5 | 7.5 | — | In-memory investigation/pending state only; no persistent state store |
| Agent Security / Threat Modeling | 3.5 | 4.5 | 8.5 | +1.0 | Prompt injection, unauthorized tools, approval boundary, evaluator-ground-truth risk, RAG trust/retrieval risks understood |
| AI Application Deployment | 3.0 | 3.5 | 7.5 | +0.5 | Lab 1 Docker deployment; newer LLM/tool/FSM/eval/retry/RAG code not yet redeployed in container/cloud |
| AI Observability / Tracing / Cost | 1.5 | 1.5 | 7.5 | — | Debug/attempt logs exist; no structured token/cost/latency tracing yet |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg)

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

Built a standalone RAG pipeline progressively:

- local security policy / IR knowledge base;
- deterministic keyword retrieval;
- bag-of-words vectors and manual cosine similarity;
- demonstrated lexical retrieval failure on `account takeover` vs `compromised account`;
- OpenAI embedding API for semantic vectors;
- observed ambiguous semantic retrieval where `doc1≈0.44` and `doc3≈0.45`;
- changed top-1 retrieval to top-2;
- added source IDs and source-attributed answers;
- added a minimum similarity threshold and verified irrelevant malware-policy query returns no document;
- precomputed document embeddings so only query embeddings are generated at query time;
- verified a grounded answer refuses to invent an unspecified password-reset wait time;
- connected the design to SOAR: RAG retrieves/contextualizes policy while deterministic controls/SOAR execute approved actions.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| RAG / Retrieval | 1.5 | 3.0 | Implemented end-to-end semantic retrieval and grounded generation with embeddings, similarity ranking, top-k, thresholding, source attribution, reusable document vectors, and negative/unsupported-detail tests |

**Why other scores did not increase:** The lab reused existing LLM API and security concepts. Retrieval was guided and limited to three short documents. No chunking, vector DB, metadata filtering, reranking, hybrid search, automated retrieval metrics, large corpus, or production indexing was implemented.

**Important design lesson:** semantic similarity is useful but not equivalent to correctness. A related document can outrank the intended one, so production RAG needs retrieval evaluation, calibrated thresholds, potentially reranking, source authorization, and grounding checks.

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
| 9 | Persistent State / Memory | Resume investigations from external state | **Next** |
| 10 | Agent Security | Prompt injection, malicious tool output, exfiltration, permission attacks | Planned |
| 11 | Observability | Trace model calls, tools, states, policy decisions, latency, tokens, cost | Planned |
| 12 | Cloud / Kubernetes Deployment | Workload identity, least privilege, secrets, network/pod controls | Planned |

---

## Lab 9 Target Architecture

```text
request / investigation
        ↓
load durable investigation state
        ↓
perform one bounded workflow step
        ↓
persist state / pending action / evidence
        ↓
process can stop or restart
        ↓
resume same investigation later
```

Lab 9 should move important state out of Python process memory so an investigation can survive restart and continue safely.

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
10. persistent state / memory         NEXT
11. deeper agent security
12. observability
13. AWS/Kubernetes deployment
```

Do not rely heavily on agent frameworks at the beginning. Implement the first versions directly enough to understand model calls, validation, state, tool execution, retry behavior, retrieval, persistence, and security boundaries before adding orchestration frameworks.

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