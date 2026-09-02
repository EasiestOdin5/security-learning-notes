# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 2, 2026  
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
| Agent Orchestration | 2.5 | 2.75 | 8.0 | +0.25 | Demonstrated a guided model → tools → model control loop, but no reusable stateful orchestrator yet |
| State Machines / Workflow Control | 2.5 | 2.5 | 8.0 | — | No explicit state machine yet |
| Deterministic Gates / Policy Controls | 3.0 | 4.75 | 8.0 | +1.75 | Input/review gates, execution allowlist, argument/policy validation, state-changing approval metadata, pending actions, and explicit approve/reject paths |
| Evaluation / Rubrics | 2.0 | 2.0 | 8.0 | — | Manual failure tests exist, but no repeatable evaluation harness |
| Self-Correction / Bounded Retry | 2.0 | 2.0 | 7.5 | — | Retry/loop risks observed but bounded retry not implemented |
| RAG / Retrieval | 1.5 | 1.5 | 7.5 | — | Not implemented |
| Agent Memory / Persistent State | 1.5 | 1.5 | 7.5 | — | In-memory pending action state was used, but persistent agent memory/state is not implemented |
| Agent Security / Threat Modeling | 3.5 | 4.5 | 8.5 | +1.0 | Prompt-injection and unauthorized-tool tests plus scoped human approval, one-time action execution, rejection, and model-vs-authorization separation |
| AI Application Deployment | 3.0 | 3.5 | 7.5 | +0.5 | Lab 1 container deployment remains demonstrated; updated LLM/tool-enabled service has not yet been redeployed in Docker |
| AI Observability / Tracing / Cost | 1.5 | 1.5 | 7.5 | — | No token/cost/latency tracing yet |

### Progress Wheel

![AI engineering progress wheel showing topics around the outside, demonstrated progress from the center, and goal levels](assets/ai-engineering-progress-wheel.svg)

The solid filled polygon is **current demonstrated progress**. The dashed outline is the target level. Topic labels and current scores are placed around the outer wheel.

---

## Evidence History

### September 1, 2026 — Baseline

The initial scores were deliberately conservative. Existing security, cloud, Kubernetes, API, identity, permissions, and trust-boundary experience provides useful transfer, but conceptual discussion of agents does not count as hands-on AI implementation.

Topics already discussed before hands-on work included agent orchestration, nondeterministic versus deterministic behavior, approval gates, state machines, rubrics, self-correction, bounded retries, tool calling, RAG, memory, and containerized alert ingestion.

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
- Demonstrated required fields, `Literal` restrictions, IP validation, and timestamp validation.
- Distinguished FastAPI, Uvicorn, ASGI, `main.py`, and the in-memory `app` object.
- Built and ran the API in Docker.
- Diagnosed a Windows `Dockerfile.txt` naming failure.
- Verified the service still worked with the host Uvicorn process stopped.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Structured Outputs / Schemas | 2.0 | 2.25 | Practical schema/type/constraint validation was demonstrated, but not yet on LLM output |
| Deterministic Gates / Policy Controls | 3.0 | 3.25 | Demonstrated deterministic input rejection before downstream application logic |
| AI Application Deployment | 3.0 | 3.5 | Built and ran a reproducible containerized service that will become the agent boundary |

---

### September 1, 2026 — Lab 2: Structured LLM Alert Triage

**Evidence:** [AI Engineering Lab 2 — Structured LLM Alert Triage](2026-09-01-lab-02-structured-llm-alert-triage.md)

Demonstrated hands-on:

- Installed and used the OpenAI Python SDK.
- Made direct Responses API calls and observed free-form output.
- Used system/user roles and environment-based API key handling.
- Defined a Pydantic `AlertTriage` model as an LLM structured-output contract.
- Added typed fields, bounded confidence, and field descriptions.
- Integrated validated FastAPI alert input with the LLM.
- Added deterministic low-confidence and API-failure gates.
- Tested an invalid API key and fixed a missing `APIError` import.
- Tested prompt injection inside untrusted alert data.
- Added an explicit `prompt_injection_detected` signal and deterministic hard review gate.
- Observed unsupported semantic specificity despite structurally valid output.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| LLM API Fundamentals | 2.0 | 2.75 | Direct SDK/API use was integrated into the application and failure behavior was tested |
| Structured Outputs / Schemas | 2.25 | 3.25 | Implemented real LLM structured output with typed constraints and security-relevant signals |
| Deterministic Gates / Policy Controls | 3.25 | 3.75 | Added deterministic low-confidence, API-failure, and prompt-injection workflow controls |
| Agent Security / Threat Modeling | 3.5 | 4.0 | Performed a prompt-injection test and corrected a policy weakness exposed by the test |

**Important limitation discovered:** Structured output constrains shape but does not guarantee semantic correctness.

---

### September 1, 2026 — Lab 3: Read-Only Investigation Tools

**Evidence:** [AI Engineering Lab 3 — Read-Only Investigation Tools](2026-09-01-lab-03-read-only-investigation-tools.md)

Demonstrated hands-on:

- Defined and exposed custom read-only investigation functions.
- Used strict JSON Schema function definitions with `tools=tools`.
- Observed actual `function_call` items and distinguished request from execution.
- Explicitly executed model-requested Python functions.
- Returned `function_call_output` associated by `call_id` and continued with `previous_response_id`.
- Added multiple tools and dynamic dispatch.
- Treated the execution registry as a deterministic allowlist.
- Exposed an unauthorized temporary tool and verified Python blocked execution.
- Added Pydantic execution-time argument models.
- Tested malformed IP arguments and application-side validation.
- Added `validate_ip_policy()` for syntactically valid but policy-disallowed IPs.
- Verified an insufficient-evidence path without invented evidence.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| LLM API Fundamentals | 2.75 | 3.0 | Demonstrated function-call continuation using `call_id`, `function_call_output`, and `previous_response_id` |
| Structured Outputs / Schemas | 3.25 | 3.5 | Added strict function-argument schemas and independent Pydantic execution-time validation |
| Tool / Function Calling | 2.0 | 3.5 | Implemented the full read-only tool lifecycle, multiple tool choices, dynamic dispatch, and result return |
| Agent Orchestration | 2.5 | 2.75 | Implemented a guided model/tool/model loop, but not a reusable stateful orchestrator |
| Deterministic Gates / Policy Controls | 3.75 | 4.25 | Added executable-tool allowlisting, argument validation, and valid-but-policy-disallowed checks |
| Agent Security / Threat Modeling | 4.0 | 4.25 | Executed an exposed-but-unauthorized tool test and preserved deterministic authorization |

**Important distinction demonstrated:** Model-facing tool availability, executable authorization, schema validity, and application policy are separate concerns.

---

### September 2, 2026 — Lab 4: Policy-Gated Tools

**Evidence:** [AI Engineering Lab 4 — Policy-Gated Tools](2026-09-02-lab-04-policy-gated-tools.md)

Demonstrated hands-on:

- Added a mock state-changing `disable_user(user)` tool.
- Changed the tool registry from tuples to named policy dictionaries.
- Added `requires_approval` metadata and distinguished read-only from approval-required execution.
- Exposed `disable_user` to the model while keeping authorization in Python.
- Verified the model could request `disable_user` but Python held it at `PENDING APPROVAL`.
- Tested an initial deterministic approval switch with both `False` and `True` paths.
- Identified that a global tool-level approval was overly broad.
- Scoped approval to tool + arguments so approval for Alice did not approve Bob.
- Demonstrated one-time approval consumption within the same Python process.
- Replaced pre-approval with `pending_actions` that stores the exact validated requested action.
- Added explicit `approve_action()` and `reject_action()` paths.
- Verified approval executes the stored action and rejection removes it without execution.
- Replaced tuple approval keys with UUID request IDs to uniquely identify action instances.
- Corrected a test still using the old tuple key after the UUID migration.
- Verified final UUID-based approval and rejection flows.
- Tested a realistic alert and observed the model investigate before proposing a state change.
- Briefly explored a multi-turn loop, observed repeated tool requests, and identified the safety/design problems of ad hoc retry/loop controls.
- Deliberately removed `while True`, duplicate-call handling, step limits, and repeat-policy logic from Lab 4 because they belong in later orchestration/state-machine work.

**Score changes:**

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Tool / Function Calling | 3.5 | 3.75 | Extended tool use from read-only evidence gathering to a state-changing action request with controlled execution |
| Deterministic Gates / Policy Controls | 4.25 | 4.75 | Implemented approval-required policy metadata, exact pending actions, scoped/one-time approval, explicit approval/rejection, and UUID action identity |
| Agent Security / Threat Modeling | 4.25 | 4.5 | Demonstrated that model intent does not grant authorization and that a human-approved exact action remains the execution boundary |

**Why other scores did not increase:** The multi-turn loop experiment was intentionally removed. There is still no explicit state machine, persistent state store, repeatable evaluation harness, bounded retry controller, or redeployed tool-enabled container. Recognizing those issues is useful but does not count as completed implementation in those skill areas.

**Important design lesson:** More model turns and more control flags are not automatically an improvement. Authorization logic should remain small and deterministic; iteration/retry semantics should be designed explicitly in the state-machine/orchestration labs.

---

# Hands-On Lab Roadmap

| Lab | Topic | Core outcome | Status |
|---:|---|---|---|
| 1 | JSON Alert Receiver | FastAPI + Pydantic + Docker deterministic boundary | **Completed** |
| 2 | Structured LLM Alert Triage | Direct LLM API call with validated structured result and deterministic review gates | **Completed** |
| 3 | Read-Only Investigation Tools | Model selects tools; Python executes validated calls | **Completed** |
| 4 | Policy-Gated Tools | Separate model intent from deterministic authorization and human approval | **Completed** |
| 5 | Investigation State Machine | Explicit states, transitions, limits, and terminal outcomes | **Next** |
| 6 | Rubrics and Evaluation | Repeatable test cases and failure categories | Planned |
| 7 | Bounded Self-Correction | Evaluate → feedback → limited retry → escalate | Planned |
| 8 | RAG | Retrieve security knowledge with source attribution | Planned |
| 9 | Persistent State / Memory | Resume investigations from external state | Planned |
| 10 | Agent Security | Prompt injection, malicious tool output, exfiltration, permission attacks | Planned |
| 11 | Observability | Trace model calls, tools, states, policy decisions, latency, tokens, and cost | Planned |
| 12 | Cloud / Kubernetes Deployment | Apply workload identity, least privilege, secrets, network and pod controls | Planned |

---

## Lab 5 Target Architecture

```text
validated alert
      ↓
INVESTIGATING
      ↓
LLM/tool decision
      ↓
more evidence? ──→ INVESTIGATING
      ↓
action proposed
      ↓
AWAITING_APPROVAL
      ↓
approve / reject
      ↓
EXECUTING / BLOCKED
      ↓
COMPLETED
```

Lab 5 should replace scattered control flags with explicit workflow state and legal transitions. It should also define terminal outcomes and bounded transitions so the agent cannot remain in an uncontrolled loop.

---

## Learning Order

```text
1. API + JSON validation              DONE
2. LLM API                            DONE
3. structured LLM outputs             DONE
4. tool calling                       DONE
5. deterministic tool-policy gates    DONE
6. state machine                      NEXT
7. evaluation/rubric
8. bounded self-correction
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