# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 3, 2026  
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
| LLM API Fundamentals | 2.0 | 3.0 | 8.0 | +1.0 | Direct Responses API use, structured parsing, function-call output continuation, environment-key handling, FastAPI integration, API-error handling |
| Structured Outputs / Schemas | 2.0 | 3.5 | 8.0 | +1.5 | Pydantic API/LLM schemas plus function-tool JSON Schema and independent application-side argument validation |
| Tool / Function Calling | 2.0 | 3.75 | 8.0 | +1.75 | Read-only and state-changing custom tools, model-selected calls, explicit execution, dynamic dispatch, result return, and approval-gated action requests |
| Agent Orchestration | 2.5 | 3.0 | 8.0 | +0.5 | Guided model/tool workflow carries an explicit investigation object across request, approval, rejection, and execution outcomes |
| State Machines / Workflow Control | 2.5 | 3.5 | 8.0 | +1.0 | Explicit FSM states, legal-transition table, deterministic enforcement, terminal states, and integrated workflow transitions |
| Deterministic Gates / Policy Controls | 3.0 | 5.0 | 8.0 | +2.0 | Input/review gates, tool allowlist, argument/policy validation, human approval, and deterministic state-transition enforcement |
| Evaluation / Rubrics | 2.0 | 3.0 | 8.0 | +1.0 | Repeatable eval harness with fixed cases, ground-truth state/tool expectations, machine-readable outcomes, PASS/FAIL summary, and intentional failure validation |
| Self-Correction / Bounded Retry | 2.0 | 2.0 | 7.5 | — | Retry/loop risks observed but bounded retry not implemented |
| RAG / Retrieval | 1.5 | 1.5 | 7.5 | — | Not implemented |
| Agent Memory / Persistent State | 1.5 | 1.5 | 7.5 | — | Investigation/pending state is in-memory only; no persistent state store |
| Agent Security / Threat Modeling | 3.5 | 4.5 | 8.5 | +1.0 | Prompt-injection, unauthorized-tool, approval-boundary, and deterministic execution-boundary tests demonstrated |
| AI Application Deployment | 3.0 | 3.5 | 7.5 | +0.5 | Lab 1 container deployment remains demonstrated; updated LLM/tool/FSM/eval version has not yet been redeployed in Docker |
| AI Observability / Tracing / Cost | 1.5 | 1.5 | 7.5 | — | No token/cost/latency tracing yet |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg)

The solid filled polygon is **current demonstrated progress**. The dashed outline is the target level. Topic labels and current scores are placed around the outer wheel.

---

## Evidence History

### September 1, 2026 — Baseline

The initial scores were deliberately conservative. Existing security, cloud, Kubernetes, API, identity, permissions, and trust-boundary experience provides useful transfer, but conceptual discussion of agents does not count as hands-on AI implementation.

**Score changes:** None.

---

### September 1, 2026 — Lab 1: FastAPI JSON Alert Receiver

**Evidence:** [AI Engineering Lab 1 — FastAPI JSON Alert Receiver](2026-09-01-lab-01-fastapi-json-alert-receiver.md)

Demonstrated FastAPI/Uvicorn setup, Pydantic alert validation, generated API documentation, Docker build/run behavior, and deterministic input rejection.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Structured Outputs / Schemas | 2.0 | 2.25 | Practical schema/type/constraint validation |
| Deterministic Gates / Policy Controls | 3.0 | 3.25 | Deterministic input rejection before application logic |
| AI Application Deployment | 3.0 | 3.5 | Built and ran the service in Docker |

---

### September 1, 2026 — Lab 2: Structured LLM Alert Triage

**Evidence:** [AI Engineering Lab 2 — Structured LLM Alert Triage](2026-09-01-lab-02-structured-llm-alert-triage.md)

Demonstrated direct Responses API use, Pydantic structured LLM output, system/user roles, confidence constraints, FastAPI integration, API-error handling, prompt-injection testing, and deterministic review gates.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| LLM API Fundamentals | 2.0 | 2.75 | Direct SDK/API integration and failure testing |
| Structured Outputs / Schemas | 2.25 | 3.25 | Real LLM structured output with typed constraints |
| Deterministic Gates / Policy Controls | 3.25 | 3.75 | Low-confidence, API-failure, and prompt-injection gates |
| Agent Security / Threat Modeling | 3.5 | 4.0 | Executed prompt-injection test and corrected policy weakness |

**Important limitation:** Structured output constrains shape but does not guarantee semantic correctness.

---

### September 1, 2026 — Lab 3: Read-Only Investigation Tools

**Evidence:** [AI Engineering Lab 3 — Read-Only Investigation Tools](2026-09-01-lab-03-read-only-investigation-tools.md)

Demonstrated custom function tools, strict JSON Schema parameters, model-selected tool calls, explicit Python execution, `function_call_output`, `call_id`, `previous_response_id`, multiple-tool dispatch, executable allowlisting, Pydantic argument validation, IP policy validation, and an insufficient-evidence test.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| LLM API Fundamentals | 2.75 | 3.0 | Function-call continuation pattern |
| Structured Outputs / Schemas | 3.25 | 3.5 | Strict function schemas and execution-time validation |
| Tool / Function Calling | 2.0 | 3.5 | Full read-only tool lifecycle and dynamic dispatch |
| Agent Orchestration | 2.5 | 2.75 | Guided model → tools → model control loop |
| Deterministic Gates / Policy Controls | 3.75 | 4.25 | Tool allowlisting, argument validation, and separate policy validation |
| Agent Security / Threat Modeling | 4.0 | 4.25 | Unauthorized-tool execution test |

---

### September 2, 2026 — Lab 4: Policy-Gated Tools

**Evidence:** [AI Engineering Lab 4 — Policy-Gated Tools](2026-09-02-lab-04-policy-gated-tools.md)

Demonstrated a state-changing `disable_user` tool, policy-aware registry metadata, human approval requirements, UUID-scoped pending actions, exact-action approval/rejection, and one-time deterministic execution. A multi-turn loop experiment was intentionally removed after exposing unnecessary complexity and repeated-call risks.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Tool / Function Calling | 3.5 | 3.75 | Extended tools from read-only evidence gathering to controlled state-changing requests |
| Deterministic Gates / Policy Controls | 4.25 | 4.75 | Explicit approval metadata, pending actions, approve/reject paths, and UUID action identity |
| Agent Security / Threat Modeling | 4.25 | 4.5 | Human-approved exact action remained the execution boundary |

---

### September 2, 2026 — Lab 5: Investigation State Machine

**Evidence:** [AI Engineering Lab 5 — Investigation State Machine](2026-09-02-lab-05-investigation-state-machine.md)

Demonstrated an explicit FSM using `Enum`, a dictionary-of-sets transition table, current-state storage, legal/illegal transition enforcement, terminal states, and integration with approval/rejection/execution paths. Tested successful approval, rejected approval, execution failure, and no-action completion. Also diagnosed API-key and missing-investigation-state integration failures.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Agent Orchestration | 2.75 | 3.0 | Same workflow object persists across request, pending approval, approval/rejection, and execution outcome |
| State Machines / Workflow Control | 2.5 | 3.5 | Real FSM with explicit states, legal/illegal transitions, terminal states, and workflow integration |
| Deterministic Gates / Policy Controls | 4.75 | 5.0 | Legal workflow transitions are enforced by deterministic Python |

**Important limitation:** The no-action completion path still uses a simplified rule: remaining in `INVESTIGATING` after the read-only result is treated as completion rather than consuming an explicit structured `investigation_complete` signal.

---

### September 3, 2026 — Lab 6: Rubrics and Evaluation

**Evidence:** [AI Engineering Lab 6 — Rubrics and Evaluation](2026-09-03-lab-06-rubrics-and-evaluation.md)

Demonstrated hands-on:

- Created a separate `eval_lab.py` evaluation module rather than appending ad hoc test calls to agent code.
- Used `@dataclass` to represent reusable `EvalCase` records.
- Defined evaluator-only ground truth for expected final state and expected tool request.
- Modified `run_request()` to return machine-readable state rather than relying only on console output.
- Captured tool names requested by the LLM and returned them for evaluation.
- Built automated state/tool comparisons and PASS/FAIL reporting.
- Added a suite-level pass counter and summary.
- Created three cases: benign completion, approval-required state change, and deterministic private-IP policy block.
- Used the eval suite to discover a Lab 5 inconsistency: policy rejection printed `BLOCKED` but did not transition the FSM to `BLOCKED`.
- Fixed the workflow so policy rejection now performs `INVESTIGATING → BLOCKED`.
- Established a clean `3/3` passing baseline.
- Deliberately changed the expected `disable_user` tool name to an incorrect value and verified the suite dropped to `2/3`, proving the harness actually detects mismatch/regression.
- Restored the expected value and verified the baseline returned to `3/3`.
- Connected the evaluation approach to familiar detection-engineering regression testing concepts.
- Identified that nondeterministic LLM evaluation will eventually require repeated runs and statistical pass rates rather than relying only on one PASS/FAIL execution.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Evaluation / Rubrics | 2.0 | 3.0 | Implemented a real reusable eval harness with fixed ground truth, machine-readable outcomes, automated PASS/FAIL, regression detection, and a suite summary |

**Why other scores did not increase:** The implementation reused the existing workflow and tools. The Lab 5 policy-state correction improves correctness but does not represent enough new state-machine or policy capability for another score increase. The evaluation set is only three guided cases with no repeated-run statistics, semantic scoring, CI, or independent large-corpus design.

**Important design lesson:** A new prompt/model/code change should not be judged only by whether a single run looks better. Run the same fixed evaluation corpus before and after the change and compare results; for nondeterministic systems, stronger evidence eventually requires repeated runs and pass-rate statistics.

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
| 7 | Bounded Self-Correction | Evaluate → feedback → limited retry → escalate | **Next** |
| 8 | RAG | Retrieve security knowledge with source attribution | Planned |
| 9 | Persistent State / Memory | Resume investigations from external state | Planned |
| 10 | Agent Security | Prompt injection, malicious tool output, exfiltration, permission attacks | Planned |
| 11 | Observability | Trace model calls, tools, states, policy decisions, latency, tokens, and cost | Planned |
| 12 | Cloud / Kubernetes Deployment | Apply workload identity, least privilege, secrets, network and pod controls | Planned |

---

## Lab 7 Target Architecture

```text
run model/agent attempt
        ↓
evaluate result against explicit criteria
        ↓
PASS ─────────────→ continue/finish
        ↓ FAIL
construct bounded feedback
        ↓
retry only if attempts remain
        ↓
PASS → continue
FAIL at limit → stop / escalate
```

Lab 7 should demonstrate that the LLM cannot retry indefinitely. Evaluation may recommend another attempt, but deterministic Python owns the retry counter and hard maximum.

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
8. bounded self-correction            NEXT
9. RAG
10. memory/state persistence
11. deeper agent security
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