# AI Engineering Hands-On Progress Tracker

**Baseline date:** September 1, 2026  
**Last updated:** September 1, 2026  
**Primary direction:** Applied / Agentic AI Engineering with a security focus  
**Scale:** 0–10, where 10 represents strong specialist-level working knowledge  
**Scoring policy:** Scores change only when a dated lab contains demonstrated implementation evidence. Discussion, recognition, architecture ideas, or correct conceptual answers alone do not increase a score.

---

## Target Outcome

Build reliable AI systems around existing foundation models rather than focus primarily on model training.

The intended engineering pattern is:

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

The long-term target is a security investigation agent that can collect evidence, select approved tools, reason over results, verify its own output against explicit criteria, and request human approval before high-risk actions.

---

## Current Progress Matrix

These scores are deliberately conservative because most AI-agent topics have been discussed conceptually but not yet implemented.

| Skill area | Initial | Current | Goal | Evidence status |
|---|---:|---:|---:|---|
| LLM API Fundamentals | 2.0 | 2.0 | 8.0 | Conceptual familiarity; no completed API lab yet |
| Structured Outputs / Schemas | 2.0 | 2.0 | 8.0 | Understands desired JSON-output pattern; not implemented |
| Tool / Function Calling | 2.0 | 2.0 | 8.0 | Understands agent→tool pattern; not implemented |
| Agent Orchestration | 2.5 | 2.5 | 8.0 | Significant conceptual interest; no working orchestrator yet |
| State Machines / Workflow Control | 2.5 | 2.5 | 8.0 | Conceptual understanding; no implemented workflow yet |
| Deterministic Gates / Policy Controls | 3.0 | 3.0 | 8.0 | Strong security intuition, but not yet implemented around an LLM |
| Evaluation / Rubrics | 2.0 | 2.0 | 8.0 | Concept discussed; no repeatable evaluation harness yet |
| Self-Correction / Bounded Retry | 2.0 | 2.0 | 7.5 | Conceptual interest; no retry controller yet |
| RAG / Retrieval | 1.5 | 1.5 | 7.5 | Limited implementation evidence |
| Agent Memory / Persistent State | 1.5 | 1.5 | 7.5 | Limited implementation evidence |
| Agent Security / Threat Modeling | 3.5 | 3.5 | 8.5 | Security background transfers well; AI-specific attacks still need practical work |
| AI Application Deployment | 3.0 | 3.0 | 7.5 | Cloud/container foundation exists; no AI service deployment yet |
| AI Observability / Tracing / Cost | 1.5 | 1.5 | 7.5 | Not yet demonstrated |

---

## Why the Baseline Is Conservative

Demonstrated strengths currently come mostly from security, cloud, Kubernetes, investigation, API reasoning, permissions, and trust-boundary thinking.

The following AI concepts have already been discussed but **do not count as implementation evidence**:

- Agent orchestration.
- Nondeterministic LLM decisions versus deterministic code.
- Approval and authorization gates.
- State machines.
- Rubrics and evaluators.
- Self-correcting / self-healing behavior.
- Bounded retry loops.
- Tool calling.
- RAG and memory.
- Containerized FastAPI as an alert-ingestion layer.

The major current gap is moving from **understanding the architecture** to **writing and testing the architecture**.

---

# Hands-On Lab Roadmap

## Phase 1 — Deterministic Application Foundation

### Lab 1 — JSON Alert Receiver

**Goal:** Build the non-AI boundary first.

Build:

```text
JSON alert
   ↓
FastAPI POST /alert
   ↓
Pydantic validation
   ↓
normalized Python object
   ↓
response
```

Demonstrate:

- FastAPI endpoint.
- Pydantic schema validation.
- Valid alert accepted.
- Missing/invalid fields rejected.
- Logging without leaking secrets.
- Docker container for the API.

**AI component:** None intentionally.

**Reason:** Establish that untrusted external input reaches deterministic validation before any LLM.

---

## Phase 2 — First LLM Integration

### Lab 2 — Structured LLM Alert Triage

Add:

```text
validated alert
      ↓
LLM API
      ↓
structured result
```

Target output:

```json
{
  "classification": "credential_abuse",
  "severity": "high",
  "needs_investigation": true,
  "confidence": 0.87
}
```

Demonstrate:

- Direct LLM API call from Python.
- System/developer instructions.
- Structured schema output.
- Programmatic parsing rather than scraping prose.
- Failure handling for invalid/refused output.
- Token and latency observation.

---

## Phase 3 — Tool Calling

### Lab 3 — Read-Only Investigation Tools

Create mocked or local tools such as:

```text
get_user_activity(user)
get_ip_reputation(ip)
get_recent_auth_events(user)
get_asset_info(host)
```

Flow:

```text
alert
 ↓
LLM decides evidence needed
 ↓
structured tool call
 ↓
Python executes tool
 ↓
result returned to LLM
```

Demonstrate:

- Tool definitions.
- Argument schema validation.
- Multiple tool choices.
- Tool result returned to the model.
- Model can conclude it has insufficient evidence.

---

## Phase 4 — Deterministic Security Gates

### Lab 4 — Policy-Gated Tools

Separate **model intent** from **authorization**.

Example:

```text
LLM requests action
       ↓
policy engine
       ├── read_logs → allow
       ├── lookup_ip → allow
       ├── disable_user → human approval
       └── delete_resource → deny
```

Demonstrate:

- Tool allowlist.
- Argument restrictions.
- Read versus write classification.
- Human-approval state.
- Hard denial independent of LLM reasoning.
- Audit log of requested versus executed actions.

This is a key bridge between existing security skills and AI engineering.

---

## Phase 5 — Explicit State Machine

### Lab 5 — Investigation Workflow Controller

Implement states similar to:

```text
RECEIVED
   ↓
TRIAGE
   ↓
COLLECT
   ↓
ANALYZE
   ↓
VERIFY
   ├── PASS → COMPLETE
   ├── MISSING_EVIDENCE → COLLECT
   └── UNSAFE / UNCERTAIN → ESCALATE
```

Demonstrate:

- State stored outside the LLM.
- Only valid transitions allowed.
- Maximum step count.
- Timeouts.
- Terminal success/failure states.
- Restart/resume behavior.

---

## Phase 6 — Rubrics and Evaluation

### Lab 6 — Deterministic + Model-Based Evaluation

Create an investigation rubric such as:

- Was alert type classified correctly?
- Were relevant tools used?
- Was evidence cited?
- Did the conclusion follow from evidence?
- Was an unsafe action attempted?
- Was uncertainty expressed when evidence was insufficient?

Build a small test dataset with expected outcomes and run the agent repeatedly.

Demonstrate:

- Pass/fail evaluation.
- Precision/accuracy-style measurements where meaningful.
- Failure categories.
- Regression testing after prompt/code changes.

---

## Phase 7 — Self-Correction Without Unbounded Autonomy

### Lab 7 — Verify and Retry

Flow:

```text
agent result
    ↓
evaluator
    ├── pass → finish
    └── fail → feedback
                  ↓
                retry
```

Constraints:

- Maximum 2–3 retries.
- No expansion of tool permissions during retry.
- Preserve evidence and failure reason.
- Escalate after retry budget is exhausted.

The objective is **bounded recovery**, not an unrestricted "self-healing" loop.

---

## Phase 8 — RAG

### Lab 8 — Security Knowledge Retrieval

Potential dataset: this `security-learning-notes` repository or a curated set of security runbooks.

Flow:

```text
documents
   ↓
chunk / index
   ↓
retrieve relevant evidence
   ↓
LLM
```

Demonstrate:

- Document ingestion.
- Retrieval.
- Source attribution.
- Retrieval quality testing.
- Behavior when no relevant source exists.
- Separation between retrieved data and trusted instructions.

---

## Phase 9 — Persistent State and Memory

### Lab 9 — Investigation Session Store

Store outside the model:

- Alert ID.
- Current workflow state.
- Tools already called.
- Evidence collected.
- Decisions made.
- Approval status.
- Retry count.

Demonstrate stopping and resuming an investigation without depending solely on conversation context.

---

## Phase 10 — Agent Security

### Lab 10 — Attack the Agent

Test:

- Prompt injection in alert text.
- Prompt injection in retrieved documents.
- Malicious tool output.
- Excessive tool calls.
- Unauthorized action requests.
- Data exfiltration attempts.
- Cross-user/state contamination.
- Secret leakage.

Demonstrate that deterministic controls still hold when the model is manipulated.

---

## Phase 11 — Observability and Production Controls

### Lab 11 — Trace an Investigation

Capture:

- Request ID / trace ID.
- Model calls.
- Tool calls.
- State transitions.
- Token use.
- Latency.
- Cost.
- Policy decisions.
- Evaluation result.
- Final disposition.

Goal: reconstruct exactly why the system behaved as it did without requiring hidden model reasoning.

---

## Phase 12 — Cloud / Kubernetes Deployment

### Lab 12 — Deploy the Security Agent Service

Evolve the earlier service into:

```text
alert producer
     ↓
API / queue
     ↓
containerized agent service
     ↓
LLM provider + tools
     ↓
persistent state / logs
```

Then apply existing cloud/Kubernetes skills:

- Workload identity.
- Least-privilege IAM/RBAC.
- Secrets management.
- NetworkPolicy.
- Pod hardening / Pod Security Admission.
- Resource limits.
- Logging and monitoring.
- CI/CD security checks.

This phase intentionally joins the AI track back to the existing AWS, Kubernetes, and DevSecOps learning tracks.

---

# Recommended Learning Order

```text
1. API + JSON validation
2. LLM API
3. structured outputs
4. tool calling
5. deterministic gates
6. state machine
7. evaluation/rubric
8. bounded self-correction
9. RAG
10. memory/state persistence
11. agent security
12. observability
13. AWS/Kubernetes deployment
```

Do **not** begin by relying heavily on agent frameworks. Implement the first versions directly enough to understand the control loop, state, tool execution, and security boundaries. Frameworks can be introduced later and evaluated against the architecture rather than becoming the architecture.

---

# Evidence Rules for Future Updates

After each lab, create a dated Markdown note under `ai-engineering/` containing:

1. Goal.
2. Architecture.
3. Commands/code used.
4. What succeeded.
5. What failed.
6. Troubleshooting performed.
7. Questions and answers.
8. Security implications.
9. What was independently understood versus completed with guidance.
10. Score changes, if justified.

A score should increase only when the lab provides new practical evidence.