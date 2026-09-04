# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 4, 2026  
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
Evaluate / bounded retry / escalate / finish
```

The long-term target is a security investigation agent that can collect evidence, select approved tools, reason over results, verify outputs against explicit criteria, use bounded correction when appropriate, and request human approval before high-risk actions.

---

## Current Progress Matrix

| Skill area | Initial | Current | Goal | Change | Evidence status |
|---|---:|---:|---:|---:|---|
| LLM API Fundamentals | 2.0 | 3.0 | 8.0 | +1.0 | Direct Responses API use, structured parsing, function-call continuation, environment-key handling, FastAPI integration, API-error handling |
| Structured Outputs / Schemas | 2.0 | 3.5 | 8.0 | +1.5 | Pydantic API/LLM schemas plus function-tool JSON Schema and independent application-side argument validation |
| Tool / Function Calling | 2.0 | 3.75 | 8.0 | +1.75 | Read-only and state-changing custom tools, model-selected calls, explicit execution, dynamic dispatch, result return, and approval-gated action requests |
| Agent Orchestration | 2.5 | 3.0 | 8.0 | +0.5 | Guided model/tool workflow carries an explicit investigation object across request, approval, rejection, and execution outcomes; multi-step tool-loop limitation remains |
| State Machines / Workflow Control | 2.5 | 3.5 | 8.0 | +1.0 | Explicit FSM states, legal-transition table, deterministic enforcement, terminal states, and integrated workflow transitions |
| Deterministic Gates / Policy Controls | 3.0 | 5.0 | 8.0 | +2.0 | Input/review gates, tool allowlist, argument/policy validation, human approval, and deterministic state-transition enforcement |
| Evaluation / Rubrics | 2.0 | 3.0 | 8.0 | +1.0 | Repeatable eval harness with fixed cases, ground-truth state/tool expectations, machine-readable outcomes, PASS/FAIL summary, and intentional failure validation |
| Self-Correction / Bounded Retry | 2.0 | 3.0 | 7.5 | +1.0 | Fixed retry budget, evaluator feedback, real LLM correction on attempt 2, real hard-stop test, and observable attempt traces |
| RAG / Retrieval | 1.5 | 1.5 | 7.5 | — | Not implemented |
| Agent Memory / Persistent State | 1.5 | 1.5 | 7.5 | — | Investigation/pending state is in-memory only; no persistent state store |
| Agent Security / Threat Modeling | 3.5 | 4.5 | 8.5 | +1.0 | Prompt-injection, unauthorized-tool, approval-boundary, deterministic execution-boundary, and evaluator-ground-truth risk discussed/tested |
| AI Application Deployment | 3.0 | 3.5 | 7.5 | +0.5 | Lab 1 container deployment remains demonstrated; updated LLM/tool/FSM/eval/retry version has not yet been redeployed in Docker |
| AI Observability / Tracing / Cost | 1.5 | 1.5 | 7.5 | — | Attempt logging exists for Lab 7 debugging, but no structured token/cost/latency tracing yet |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg)

The solid filled polygon is **current demonstrated progress**. The dashed outline is the target level. Topic labels and current scores are placed around the outer wheel.

---

## Evidence History

### September 1, 2026 — Baseline

Initial scores were deliberately conservative. Existing security, cloud, Kubernetes, API, identity, permissions, and trust-boundary experience provides useful transfer, but conceptual discussion of agents does not count as hands-on AI implementation.

**Score changes:** None.

---

### September 1, 2026 — Lab 1: FastAPI JSON Alert Receiver

**Evidence:** [AI Engineering Lab 1 — FastAPI JSON Alert Receiver](2026-09-01-lab-01-fastapi-json-alert-receiver.md)

Demonstrated FastAPI/Uvicorn setup, Pydantic alert validation, generated API documentation, Docker build/run behavior, and deterministic input rejection.

**Score changes:** Structured Outputs / Schemas 2.0→2.25; Deterministic Gates 3.0→3.25; Deployment 3.0→3.5.

---

### September 1, 2026 — Lab 2: Structured LLM Alert Triage

**Evidence:** [AI Engineering Lab 2 — Structured LLM Alert Triage](2026-09-01-lab-02-structured-llm-alert-triage.md)

Demonstrated direct Responses API use, Pydantic structured LLM output, system/user roles, confidence constraints, FastAPI integration, API-error handling, prompt-injection testing, and deterministic review gates.

**Score changes:** LLM API 2.0→2.75; Structured Outputs 2.25→3.25; Deterministic Gates 3.25→3.75; Agent Security 3.5→4.0.

**Important limitation:** Structured output constrains shape but does not guarantee semantic correctness.

---

### September 1, 2026 — Lab 3: Read-Only Investigation Tools

**Evidence:** [AI Engineering Lab 3 — Read-Only Investigation Tools](2026-09-01-lab-03-read-only-investigation-tools.md)

Demonstrated custom function tools, strict JSON Schema parameters, model-selected tool calls, explicit Python execution, `function_call_output`, `call_id`, `previous_response_id`, multiple-tool dispatch, executable allowlisting, Pydantic argument validation, IP policy validation, and an insufficient-evidence test.

**Score changes:** LLM API 2.75→3.0; Structured Outputs 3.25→3.5; Tool Calling 2.0→3.5; Orchestration 2.5→2.75; Deterministic Gates 3.75→4.25; Agent Security 4.0→4.25.

---

### September 2, 2026 — Lab 4: Policy-Gated Tools

**Evidence:** [AI Engineering Lab 4 — Policy-Gated Tools](2026-09-02-lab-04-policy-gated-tools.md)

Demonstrated a state-changing `disable_user` tool, policy-aware registry metadata, human approval requirements, UUID-scoped pending actions, exact-action approval/rejection, and one-time deterministic execution. A multi-turn loop experiment was intentionally removed after exposing unnecessary complexity and repeated-call risks.

**Score changes:** Tool Calling 3.5→3.75; Deterministic Gates 4.25→4.75; Agent Security 4.25→4.5.

---

### September 2, 2026 — Lab 5: Investigation State Machine

**Evidence:** [AI Engineering Lab 5 — Investigation State Machine](2026-09-02-lab-05-investigation-state-machine.md)

Demonstrated an explicit FSM using `Enum`, a dictionary-of-sets transition table, current-state storage, legal/illegal transition enforcement, terminal states, and integration with approval/rejection/execution paths. Tested successful approval, rejected approval, execution failure, and no-action completion.

**Score changes:** Orchestration 2.75→3.0; State Machines 2.5→3.5; Deterministic Gates 4.75→5.0.

**Important limitation:** The no-action completion path still treats remaining in `INVESTIGATING` after the read-only result as completion rather than consuming an explicit structured `investigation_complete` signal.

---

### September 3, 2026 — Lab 6: Rubrics and Evaluation

**Evidence:** [AI Engineering Lab 6 — Rubrics and Evaluation](2026-09-03-lab-06-rubrics-and-evaluation.md)

Created `eval_lab.py`, reusable `EvalCase` records, evaluator-only expected state/tool ground truth, machine-readable `run_request()` results, automated PASS/FAIL checks, and a suite summary. A three-case baseline reached `3/3`. Deliberately corrupting the expected tool name reduced the suite to `2/3`, proving the harness detects mismatches. The eval also found a real Lab 5 defect where a policy rejection printed `BLOCKED` without actually transitioning the FSM; that was corrected.

**Score changes:** Evaluation / Rubrics 2.0→3.0.

**Important design lesson:** Evaluation ground truth is test data, not an LLM hint. For nondeterministic systems, stronger future evaluation should use repeated runs and pass-rate statistics.

---

### September 4, 2026 — Lab 7: Bounded Self-Correction

**Evidence:** [AI Engineering Lab 7 — Bounded Self-Correction](2026-09-04-lab-07-bounded-self-correction.md)

Demonstrated hands-on:

- Built a retry controller with deterministic `MAX_ATTEMPTS = 2`.
- Proved a basic fake failure→retry→success path.
- Recognized that a counter-driven fake success is retry behavior, not self-correction.
- Changed evaluator output to `(passed, feedback)` and passed the feedback into the next attempt.
- Tightened the fake runner so only specific expected feedback changes behavior.
- Verified a bad/unrecognized feedback path fails twice and stops at the hard limit.
- Wrapped the existing investigation agent and tested state/tool expectations.
- Corrected an invalid evaluator assumption: `Investigate whether user alice should be disabled` reasonably produced `get_user_activity` and `COMPLETED`; forcing `disable_user` was not valid ground truth.
- Verified an explicit evidence+policy prompt correctly requested `disable_user` and entered `AWAITING_APPROVAL`.
- Identified an existing orchestration limitation: after a read-only tool result, the current single-pass agent does not continue into another full tool-call cycle such as `get_user_activity → disable_user`.
- Intentionally did not add a general while-loop because multi-step tool orchestration had already caused repeated-call complexity in Lab 4.
- Isolated self-correction with a plain LLM response so tool orchestration would not obscure the mechanism.
- Used a deterministic evaluator requiring exactly `SAFE`.
- Ran a real prompt that produced a verbose first answer, returned explicit evaluator feedback, and observed the real LLM correct attempt 2 to exactly `SAFE`.
- Added logging showing exact attempt input, model output, evaluator decision, and feedback.
- Made the evaluator intentionally impossible to satisfy and verified the real LLM failed both attempts and the controller stopped at `MAX_ATTEMPTS`.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Self-Correction / Bounded Retry | 2.0 | 3.0 | Implemented and tested a real bounded feedback→retry mechanism, including successful real-LLM correction and deterministic hard-stop behavior |

**Why other scores did not increase:** Lab 7 reused the Lab 6 evaluator concept rather than materially expanding evaluation. Agent orchestration was not improved; a limitation was found and deliberately left for a later advanced pass. Debug prints do not yet constitute production observability.

**Important design lesson:** self-correction is not “let the model keep trying.” Deterministic code owns the retry budget; the evaluator identifies what failed; the model may use that feedback on the next allowed attempt. Incorrect evaluator ground truth can also push a model toward an unjustified action, so the rubric itself is part of the safety boundary.

---

# Hands-On Lab Roadmap

| Lab | Topic | Core outcome | Status |
|---:|---|---|---|
| 1 | JSON Alert Receiver | FastAPI + Pydantic + Docker deterministic boundary | **Completed** |
| 2 | Structured LLM Alert Triage | Direct LLM API call with validated structured result and deterministic review gates | **Completed** |
| 3 | Read-Only Investigation Tools | Model selects tools; Python executes validated calls | **Completed** |
| 4 | Policy-Gated Tools | Separate model intent from deterministic authorization and human approval | **Completed** |
| 5 | Investigation State Machine | Explicit states, legal transitions, terminal outcomes, and workflow integration | **Completed** |
| 6 | Rubrics and Evaluation | Repeatable test cases, expected outcomes, automated PASS/FAIL, and regression baseline | **Completed** |
| 7 | Bounded Self-Correction | Evaluate → feedback → limited retry → hard stop | **Completed** |
| 8 | RAG | Retrieve security knowledge with source attribution | **Next** |
| 9 | Persistent State / Memory | Resume investigations from external state | Planned |
| 10 | Agent Security | Prompt injection, malicious tool output, exfiltration, permission attacks | Planned |
| 11 | Observability | Trace model calls, tools, states, policy decisions, latency, tokens, and cost | Planned |
| 12 | Cloud / Kubernetes Deployment | Apply workload identity, least privilege, secrets, network and pod controls | Planned |

---

## Lab 8 Target Architecture

```text
user / investigation question
        ↓
retrieve relevant trusted documents
        ↓
select useful passages
        ↓
provide retrieved context to LLM
        ↓
LLM answers from supplied evidence
        ↓
include source attribution
```

Lab 8 should introduce retrieval without hiding the mechanics behind a large agent framework. The first goal is to understand document chunks, retrieval relevance, context injection, and grounding before adding more elaborate vector infrastructure.

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
9. RAG                                NEXT
10. memory/state persistence
11. deeper agent security
12. observability
13. AWS/Kubernetes deployment
```

Do not rely heavily on agent frameworks at the beginning. Implement the first versions directly enough to understand model calls, schema validation, state, tool execution, retry behavior, retrieval, and security boundaries before adding orchestration frameworks.

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