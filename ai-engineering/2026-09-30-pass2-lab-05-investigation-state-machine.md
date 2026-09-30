# Pass 2 — Lab 5: Investigation State Machine

**Date completed:** September 30, 2026  
**Status:** Completed  
**Pass:** Pass 2 — guided design, increasingly independent implementation

---

## Goal

Replace loose workflow status handling with an explicit finite-state machine (FSM) so investigation transitions are deterministic and illegal transitions are rejected.

The implemented investigation states are:

```text
NEW
INVESTIGATING
AWAITING_APPROVAL
EXECUTING
COMPLETED
BLOCKED
```

The main legal paths are:

```text
NEW → INVESTIGATING → COMPLETED

NEW → INVESTIGATING → BLOCKED

NEW → INVESTIGATING → AWAITING_APPROVAL → BLOCKED

NEW → INVESTIGATING → AWAITING_APPROVAL
    → EXECUTING → COMPLETED

NEW → INVESTIGATING → AWAITING_APPROVAL
    → EXECUTING → BLOCKED
```

---

## FSM Module

The state machine was separated into a new `investigation_state.py` file.

```python
from enum import Enum

class InvestigationState(str, Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    BLOCKED = "blocked"
```

Using `str, Enum` keeps the states explicit while making them convenient to serialize through FastAPI/JSON.

---

## Allowed Transition Table

The legal transition graph was represented directly in Python:

```python
ALLOWED_TRANSITIONS = {

    InvestigationState.NEW: {
        InvestigationState.INVESTIGATING
    },

    InvestigationState.INVESTIGATING: {
        InvestigationState.AWAITING_APPROVAL,
        InvestigationState.COMPLETED,
        InvestigationState.BLOCKED
    },

    InvestigationState.AWAITING_APPROVAL: {
        InvestigationState.EXECUTING,
        InvestigationState.BLOCKED
    },

    InvestigationState.EXECUTING: {
        InvestigationState.COMPLETED,
        InvestigationState.BLOCKED
    },

    InvestigationState.COMPLETED: set(),

    InvestigationState.BLOCKED: set(),
}
```

`COMPLETED` and `BLOCKED` are terminal states.

A design correction was made during implementation: `INVESTIGATING → EXECUTING` was initially allowed, but that would bypass the approval boundary. It was removed so execution can occur only after `AWAITING_APPROVAL`.

---

## Centralized Transition Enforcement

All state changes go through one function:

```python
def transition_to(
    current_state: InvestigationState,
    target_state: InvestigationState
):
    if current_state not in ALLOWED_TRANSITIONS:
        raise ValueError(
            f"Unknown or unmapped current state: '{current_state}'"
        )

    allowed_next = ALLOWED_TRANSITIONS[current_state]

    if target_state not in allowed_next:
        raise ValueError(
            f"Cannot transition directly from "
            f"'{current_state.value}' to '{target_state.value}'"
        )

    return target_state
```

This makes the rule explicit:

```text
caller proposes target state
        ↓
transition_to()
        ↓
allowed? → return target state
illegal? → raise ValueError
```

---

## Why ValueError Instead of HTTPException in the FSM Module

The FSM module originally imported FastAPI and raised `HTTPException` directly.

That would work technically, but it couples the state machine to the web framework.

The cleaner separation is:

```text
investigation_state.py
→ workflow/business logic
→ raises ValueError

main.py
→ HTTP/API layer
→ catches ValueError
→ raises HTTPException
```

Example integration:

```python
try:
    current_state = transition_to(
        current_state,
        InvestigationState.INVESTIGATING
    )
except ValueError as e:
    raise fastapi.HTTPException(
        status_code=400,
        detail=str(e)
    )
```

The issue was architectural dependency direction, not any Python limitation with imports.

---

## Investigation Start

At the beginning of `/investigate`:

```python
current_state = InvestigationState.NEW
```

The workflow immediately transitions:

```text
NEW → INVESTIGATING
```

using `transition_to()`.

This establishes an explicit state from the start of the request rather than relying on implicit control flow.

---

## Approval-Required Tool Path

When policy identifies a state-changing tool such as `disable_user` as `approval_required`, the investigation moves:

```text
INVESTIGATING → AWAITING_APPROVAL
```

before the pending action is stored.

The pending action now includes:

```python
pending_action["investigation_state"] = current_state
```

This is necessary because `current_state` inside `/investigate` is local. The later `/approve` and `/reject` requests need durable access to the state associated with that pending action.

A single global `current_state` was deliberately avoided because multiple investigations could overwrite one another.

---

## Approval Path

The approval endpoint retrieves the state from the exact pending action.

Before the tool runs:

```text
AWAITING_APPROVAL → EXECUTING
```

The action status is also changed to:

```text
executing
```

Then the actual tool is called.

If the tool succeeds:

```text
EXECUTING → COMPLETED
status = executed
```

If execution raises an exception:

```text
EXECUTING → BLOCKED
status = blocked
```

This ordering matters because the state should describe the workflow **while** the execution attempt is happening, not only after it finishes.

---

## Reject Path

If a pending action is rejected:

```text
AWAITING_APPROVAL → BLOCKED
status = rejected
```

The state transition is wrapped with the same `ValueError → HTTPException` translation used elsewhere.

The high-impact tool is never executed on this path.

---

## Investigation Completion Without Approval

An investigation that never creates a pending high-impact action should not remain stuck in `INVESTIGATING`.

At the end of `/investigate`:

```python
if current_state == InvestigationState.INVESTIGATING:
    current_state = transition_to(
        current_state,
        InvestigationState.COMPLETED
    )
```

This gives the no-approval path:

```text
NEW → INVESTIGATING → COMPLETED
```

The resulting investigation state was also added to the API response so the workflow can be verified externally.

---

## Investigation State vs Pending Action Status

A key design question was why both fields exist.

### `investigation_state`

Represents the overall workflow:

```text
NEW
INVESTIGATING
AWAITING_APPROVAL
EXECUTING
COMPLETED
BLOCKED
```

### `status`

Represents the specific pending action record:

```text
waiting_for_approval
executing
executed
rejected
blocked
```

They overlap in this small lab, but they are not conceptually identical.

In a larger design, one investigation could contain multiple actions. One action may already be `executed` while the overall investigation is still `INVESTIGATING`.

The tradeoff is that two fields add synchronization overhead. For this lab they were kept separate to preserve the distinction between workflow state and action status.

---

## Questions and Answers

### Should the FSM be in a new file?

Yes. The design used:

```text
investigation_tools.py
→ tool implementations + argument models

investigation_state.py
→ states + legal transitions

main.py
→ FastAPI + orchestration
```

This keeps responsibilities clearer.

### Was asking for the possible paths reasonable?

Yes. The exact transition graph is a design decision, not a Python fact with one universal answer. A future independence goal is to propose the transition table first and then have it reviewed.

### Why not allow INVESTIGATING → EXECUTING?

Because that would bypass the human-approval boundary. A high-impact action should reach `EXECUTING` only from `AWAITING_APPROVAL`.

### Why raise instead of silently returning the old state?

Silently returning the current state can hide workflow bugs. Raising makes an illegal transition observable and testable.

### Why not raise HTTPException directly in investigation_state.py?

It would work, but it couples core workflow logic to FastAPI. Raising `ValueError` keeps the FSM reusable from an API, CLI, worker, or unit test.

### Does Python have a problem importing FastAPI into the FSM file?

No. The issue is architectural coupling, not import mechanics.

### Why is current_state not global?

A single global current state would not scale to multiple investigations. State belongs to a specific investigation/action record.

### Why transition to EXECUTING before calling the tool?

Because the workflow is already in the execution phase once the approved operation begins.

### How do we know execution succeeded?

For the current lab tool, returning normally from the function is enough. In a real external API, success might also require checking the returned status/result because some APIs report failure as data rather than raising.

### Why keep both investigation_state and status?

They represent different scopes: overall investigation workflow versus one pending action. The distinction becomes more important when an investigation contains multiple actions.

### Why was `except Exception: raise` removed?

That pattern catches every exception and immediately re-raises the same exception unchanged, so it adds no behavior. Where transition errors are expected, the useful pattern is:

```python
except ValueError as e:
    raise fastapi.HTTPException(...)
```

### Could the try/except have simply been changed instead of removed?

Yes. The cleaner correction was to preserve the structure and replace the generic exception handling with explicit `ValueError` handling.

### Why does the implementation feel heavy?

The FSM itself is small. Most of the code volume comes from integration:

- duplicated tool-processing loops;
- pending-action storage;
- separate action status and investigation state;
- HTTP exception translation;
- approve/reject endpoints;
- keeping state synchronized across multiple request paths.

The code currently emphasizes explicit boundaries and learning clarity over elegance. A later refactor should centralize repeated transition/tool-processing behavior.

---

## Verification

### Approval path

A severe Alice account-compromise scenario was submitted that caused `disable_user` to be requested.

Observed path:

```text
NEW
→ INVESTIGATING
→ AWAITING_APPROVAL
→ EXECUTING
→ COMPLETED
```

The approval response exposed:

```text
investigation_state = completed
```

### Rejection path

A fresh pending action was rejected.

Observed path:

```text
NEW
→ INVESTIGATING
→ AWAITING_APPROVAL
→ BLOCKED
```

The rejection response exposed:

```text
investigation_state = blocked
```

### Illegal transition test

The FSM was directly tested with:

```python
transition_to(
    InvestigationState.NEW,
    InvestigationState.COMPLETED
)
```

Observed result:

```text
ValueError:
Cannot transition directly from 'new' to 'completed'
```

This directly demonstrated that illegal transitions are rejected rather than silently accepted.

---

## What Was Independent vs Guided

### Independent / demonstrated

- created the `InvestigationState` enum;
- created the transition-table data structure;
- implemented centralized transition validation;
- integrated the FSM into the existing investigation workflow;
- recognized that state must survive beyond the local `/investigate` function;
- stored investigation state with the pending action instead of using one global variable;
- integrated approve success and failure transitions;
- integrated reject/block transition;
- synchronized action status with investigation state;
- exposed states in API responses for verification;
- successfully exercised approval and rejection terminal paths;
- directly tested an illegal transition and observed the expected `ValueError`.

### Guided / corrected

- initial list of states and legal paths was supplied;
- corrected a typo in `COMPLETED`;
- corrected an initially allowed `INVESTIGATING → EXECUTING` transition;
- recommended raising instead of silently retaining the old state;
- recommended separating FSM `ValueError` from FastAPI `HTTPException`;
- guided where to persist investigation state;
- corrected the order so `AWAITING_APPROVAL → EXECUTING` happens before tool execution;
- corrected `EXECUTED` to the actual terminal FSM state `COMPLETED`;
- suggested exposing state values in endpoint responses so testing was observable.

---

## Remaining Limitations

- state is still stored only in memory through `pending_actions`;
- investigation state is attached to a pending action rather than represented by a dedicated investigation object;
- action status and investigation state can drift if future code updates one but not the other;
- the duplicated tool-processing loops make transition handling repetitive;
- broad `except Exception` around tool execution still mixes tool failure with possible downstream workflow errors;
- no concurrency controls or transactions protect state changes;
- no explicit structured LLM signal currently decides that an investigation is complete; the no-action path is still simplified;
- no automated FSM test suite yet; verification was manual.

These are later refinement/evaluation concerns rather than blockers for this lab.

---

## Conservative Score Changes

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Agent Orchestration | 3.5 | 3.75 | Integrated explicit workflow state across investigate, approve, reject, success, and failure paths |
| State Machines / Workflow Control | 3.5 | 4.0 | Rebuilt explicit states, transition table, centralized enforcement, terminal paths, API integration, and direct illegal-transition verification |
| Deterministic Gates / Policy Controls | 6.25 | 6.5 | Approval/rejection policy is now enforced together with explicit legal workflow transitions rather than status strings alone |

No Tool Calling, Security, Persistence, or Structured Output score increase was awarded because this lab primarily demonstrated workflow-control implementation.

---

## Main Takeaway

The application no longer depends only on incidental control flow or loose status strings.

It now has an explicit rule:

```text
current state
    ↓
requested next state
    ↓
transition_to()
    ↓
legal → transition
illegal → reject
```

The most important architectural distinction is that the FSM controls **which workflow transitions are legal**, while the policy layer controls **whether a requested capability may execute**. Together they form two separate deterministic boundaries around model-driven behavior.
