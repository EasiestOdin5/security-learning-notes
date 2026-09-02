# AI Engineering Lab 5 — Investigation State Machine

**Date:** September 2, 2026  
**Status:** Completed  
**Primary objective:** Replace scattered workflow assumptions with explicit states and legal transitions enforced by Python.

---

## Goal

Model the security investigation workflow as a finite state machine (FSM) so the LLM or surrounding application cannot arbitrarily jump between workflow phases.

Target workflow:

```text
NEW
  ↓
INVESTIGATING
  ├──→ AWAITING_APPROVAL
  │          ├──→ EXECUTING ──→ COMPLETED
  │          │                    └─ execution failure → BLOCKED
  │          └──→ BLOCKED
  ├──→ COMPLETED
  └──→ BLOCKED
```

The central rule is:

> The reasoning layer may determine what should happen next, but Python enforces whether that state transition is legal.

---

## 1. Defined Explicit Investigation States

Created `state_machine.py`:

```python
from enum import Enum


class InvestigationState(Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    BLOCKED = "blocked"
```

Meaning of each state:

- `NEW`: investigation exists but has not started.
- `INVESTIGATING`: evidence gathering / read-only investigation is occurring.
- `AWAITING_APPROVAL`: a state-changing action has been proposed and is waiting for authorization.
- `EXECUTING`: an approved state-changing action is actually running.
- `COMPLETED`: the workflow finished successfully or no further action is needed.
- `BLOCKED`: the workflow stopped because policy, rejection, safety, or execution failure prevented continuation.

---

## 2. Defined Legal Transitions

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

### Conceptual interpretation

`ALLOWED_TRANSITIONS` is a dictionary whose keys are current states and whose values are sets of legal next states.

It is best understood as an adjacency-list representation of a directed graph, not as a linked list.

For example:

```text
NEW → {INVESTIGATING}
```

means `NEW` has one legal outgoing edge.

```text
INVESTIGATING → {
    AWAITING_APPROVAL,
    COMPLETED,
    BLOCKED
}
```

means an investigation may take one of three legal paths depending on what the investigation determines.

---

## 3. Added Transition Enforcement

```python
class Investigation:
    def __init__(self):
        self.state = InvestigationState.NEW

    def transition_to(self, new_state):
        allowed = ALLOWED_TRANSITIONS[self.state]

        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {new_state.value}"
            )

        print(
            f"STATE: {self.state.value} -> {new_state.value}"
        )

        self.state = new_state
```

This converted the transition table from documentation into an enforceable control.

---

## 4. Tested Illegal Transition

Tested:

```text
NEW → INVESTIGATING → EXECUTING
```

Observed:

```text
STATE: new -> investigating
ValueError: Invalid transition: investigating -> executing
```

This proved the workflow cannot skip `AWAITING_APPROVAL` and jump directly from investigation into execution.

---

## 5. Tested Full Legal Path

Tested:

```text
NEW
→ INVESTIGATING
→ AWAITING_APPROVAL
→ EXECUTING
→ COMPLETED
```

Observed:

```text
STATE: new -> investigating
STATE: investigating -> awaiting_approval
STATE: awaiting_approval -> executing
STATE: executing -> completed
```

---

## 6. Tested Terminal-State Enforcement

After reaching `COMPLETED`, attempted to transition back to `INVESTIGATING`.

Observed:

```text
ValueError: Invalid transition: completed -> investigating
```

Because `COMPLETED` and `BLOCKED` map to empty sets, they are terminal states in the current design.

---

## 7. Made the State-Machine Module Import-Safe

Moved local test code under:

```python
if __name__ == "__main__":
```

This allows `test_tool.py` to import the FSM definitions without automatically running the state-machine test code.

---

## 8. Connected the FSM to the Existing Agent Workflow

Imported the state-machine classes into `test_tool.py`:

```python
from state_machine import Investigation, InvestigationState
```

At the start of each request:

```python
investigation = Investigation()

investigation.transition_to(
    InvestigationState.INVESTIGATING
)
```

A state-changing request requiring approval now transitions:

```python
investigation.transition_to(
    InvestigationState.AWAITING_APPROVAL
)
```

The exact investigation object is stored with the pending action:

```python
pending_actions[request_id] = {
    "tool": item.name,
    "function": function,
    "args": validated_args,
    "investigation": investigation
}
```

This is important because approval or rejection must continue the same workflow instance rather than creating a new investigation.

---

## 9. Approval Path

Updated `approve_action()` so approval advances the same investigation:

```python
def approve_action(request_id):

    if request_id not in pending_actions:
        print("NO PENDING ACTION")
        return

    action = pending_actions.pop(request_id)
    investigation = action["investigation"]

    investigation.transition_to(
        InvestigationState.EXECUTING
    )

    try:
        result = action["function"](**action["args"])

    except Exception as e:
        investigation.transition_to(
            InvestigationState.BLOCKED
        )

        print("EXECUTION FAILED:", e)
        return

    investigation.transition_to(
        InvestigationState.COMPLETED
    )

    print("APPROVED AND EXECUTED:", result)
```

Successful test:

```text
STATE: new -> investigating
STATE: investigating -> awaiting_approval
PENDING APPROVAL: ... disable_user {'user': 'alice'}
STATE: awaiting_approval -> executing
STATE: executing -> completed
APPROVED AND EXECUTED: {'user': 'alice', 'status': 'disabled'}
```

Important distinction: approval does not cause the LLM to execute the action. `approve_action()` is deterministic Python code that executes the stored function.

---

## 10. Rejection Path

Updated `reject_action()`:

```python
def reject_action(request_id):

    if request_id not in pending_actions:
        print("NO PENDING ACTION")
        return

    action = pending_actions.pop(request_id)
    investigation = action["investigation"]

    investigation.transition_to(
        InvestigationState.BLOCKED
    )

    print("REJECTED:", request_id)
```

Observed:

```text
STATE: new -> investigating
STATE: investigating -> awaiting_approval
PENDING APPROVAL: ... disable_user {'user': 'bob'}
STATE: awaiting_approval -> blocked
REJECTED: ...
```

---

## 11. Execution-Failure Path

Temporarily modified the mock state-changing tool:

```python
def disable_user(user: str):

    if user == "fail-user":
        raise RuntimeError("simulated_execution_failure")

    return {
        "user": user,
        "status": "disabled"
    }
```

Then approved `disable_user("fail-user")`.

Observed:

```text
STATE: new -> investigating
STATE: investigating -> awaiting_approval
STATE: awaiting_approval -> executing
STATE: executing -> blocked
EXECUTION FAILED: simulated_execution_failure
```

This demonstrated that approval and successful execution are separate events. An approved action can still fail and terminate in `BLOCKED`.

---

## 12. No-Action Completion Path

For user `bob`, the mock read-only evidence returned:

```text
failed_logins: 0
successful_logins: 1
last_source_ip: None
```

The model responded that there was no apparent suspicious activity and no action was taken.

The workflow then transitioned:

```text
STATE: investigating -> completed
```

### Current limitation

The current Python implementation marks the workflow `COMPLETED` when the request finishes while still in `INVESTIGATING`.

That is useful for this FSM lab, but it is not yet a strong decision contract. A better later design is for the reasoning layer to return an explicit structured signal such as:

```text
investigation_complete = true
action_needed = false
```

Python can then use that explicit signal to request the legal transition to `COMPLETED`.

---

# Questions and Answers

## Is `ALLOWED_TRANSITIONS` like a linked list?

No. It is closer to a directed graph represented as an adjacency list. Each state can point to zero, one, or multiple legal next states.

## From `NEW`, can we only go to `INVESTIGATING`?

Yes. That is intentional. A new investigation cannot legally jump directly into approval, execution, completion, or blocked state.

## Why can `INVESTIGATING` transition to three states?

Because investigation can end in three broad ways:

1. Action is required → `AWAITING_APPROVAL`.
2. No further action is needed → `COMPLETED`.
3. Policy/security prevents safe continuation → `BLOCKED`.

## What does `AWAITING_APPROVAL → EXECUTING` mean?

The pending state-changing action was approved, so Python is now permitted to run it. For this lab, that action was `disable_user(user)`.

## What does `AWAITING_APPROVAL → BLOCKED` mean?

The proposed action was rejected, denied, expired, or otherwise not authorized.

## Why is `BLOCKED` also reachable from `INVESTIGATING` and `EXECUTING`?

It is the same terminal state with different causes:

- `INVESTIGATING → BLOCKED`: usually security or policy stopped the investigation.
- `AWAITING_APPROVAL → BLOCKED`: authorization was denied.
- `EXECUTING → BLOCKED`: the approved action failed or encountered an execution-time safety/error condition.

A future refinement should store a separate `blocked_reason` so the terminal cause is explicit.

## Is `EXECUTING` the same thing as `disable_user()`?

No. `EXECUTING` is a workflow phase. `disable_user()` is one particular action that may run while the investigation is in that state.

## Is this a common code structure?

Yes. This is a basic finite state machine implementation: an Enum defines states, a transition table defines legal edges, an object stores the current state, and a transition function enforces movement between states.

## Is FSM basic Python?

FSM is not a Python feature. The implementation uses basic/intermediate Python constructs such as Enum, dictionaries, sets, classes, and exceptions, but FSM itself is a general software-design concept.

## How advanced is FSM as software design?

A basic explicit FSM is generally intermediate software design. It becomes substantially more advanced with nested states, concurrency, retries, timers, persistence, distributed execution, and crash recovery.

## Once an action is approved, does the LLM execute it?

No. The LLM proposed the action earlier. After approval, deterministic Python retrieves the stored function and arguments and executes them.

## How does the current no-action path decide to complete?

At present, if the request finishes and the investigation has not left `INVESTIGATING`, Python treats that as completion. This is intentionally documented as a temporary simplification rather than a robust semantic decision rule.

---

# Troubleshooting / Failures

## Invalid OpenAI API key

The first integrated test reached:

```text
STATE: new -> investigating
```

but the Responses API returned HTTP 401 `invalid_api_key`.

The environment variable was corrected in CMD and the test was rerun successfully.

## Missing investigation in pending action

The first FSM-connected approval test failed with:

```text
KeyError: 'investigation'
```

The pending action still used the older Lab 4 dictionary and did not contain the FSM object.

Fixed by adding:

```python
"investigation": investigation
```

This reinforced that the approval handler must resume the same investigation instance.

---

# Security / Design Lessons

1. Legal workflow transitions should be deterministic rather than left to model behavior.
2. Approval is a state transition, not permission for the LLM itself to execute code.
3. State-changing actions should not be reachable directly from `NEW` or `INVESTIGATING` without the required intermediate authorization state.
4. Terminal states prevent accidental reuse of a finished workflow.
5. The same terminal outcome can represent different causes; later designs should record explicit reason metadata.
6. Approval does not guarantee successful execution, so execution failure requires its own transition path.
7. Explicit workflow state is clearer and safer than accumulating unrelated booleans and `if/else` flags.
8. The current implicit completion rule is deliberately limited; semantic completion should later be represented by a structured decision.

---

# What Was Demonstrated vs. Still Guided

## Demonstrated

- Understood states as nodes and transitions as directed edges.
- Correctly interpreted the transition table and multiple outgoing transitions.
- Tested legal, illegal, and terminal transitions.
- Connected FSM state to an existing LLM/tool approval workflow.
- Preserved the same investigation object across pending approval.
- Tested successful approval, rejection, execution failure, and no-action completion.
- Distinguished workflow state from tool/action execution.

## Still guided

- FSM structure and integration code were supplied incrementally.
- State design was not created independently from scratch.
- Completion semantics are still simplified.
- No transition events, guards beyond legal-state membership, transition counters, retry semantics, persistent state, or recovery behavior are implemented yet.

---

# Lab 5 Result

Lab 5 is complete.

The workflow now has an explicit deterministic state model rather than only scattered control logic:

```text
NEW
→ INVESTIGATING
→ AWAITING_APPROVAL / COMPLETED / BLOCKED
→ EXECUTING / BLOCKED
→ COMPLETED / BLOCKED
```

This provides the control-flow foundation for the next lab: repeatable rubrics and evaluation.