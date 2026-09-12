# AI Engineering Lab 9 — Persistent State / Memory

**Date:** September 12, 2026  
**Status:** Completed  
**Primary file:** `memory_lab.py`  
**Supporting files:** `state_machine.py`, `main.py`

---

## Goal

Move important agent workflow state out of process-local Python memory so an investigation can survive a process restart and safely resume later.

The first-pass architecture was deliberately small:

```text
investigation / pending action
        ↓
persist to SQLite
        ↓
process can exit/restart
        ↓
load state from SQLite
        ↓
reconstruct trusted Python objects/functions
        ↓
continue legal workflow transition
```

The lab focused on durable workflow state rather than conversational memory.

---

## Core Implementation

### 1. SQLite database

Created a local SQLite database:

```text
agent_state.db
```

The initial schema stored investigation state:

```sql
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL
)
```

Later a second table was added for pending approval actions:

```sql
CREATE TABLE IF NOT EXISTS pending_actions (
    request_id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_json TEXT NOT NULL
)
```

`connection.commit()` was used after writes so the transaction becomes durable.

### 2. Persist and reload investigations

Implemented `save_investigation()` and `load_investigation()`.

Demonstrated:

```text
investigation-001 → investigating
```

then updated it to:

```text
investigation-001 → awaiting_approval
```

and successfully read the state back on later script runs.

### 3. Reconstruct the FSM

Updated the `Investigation` constructor so an existing state can be restored:

```python
class Investigation:
    def __init__(self, state=InvestigationState.NEW):
        self.state = state
```

A persisted string such as:

```text
awaiting_approval
```

was converted back to:

```python
InvestigationState.AWAITING_APPROVAL
```

and used to reconstruct the actual workflow object.

### 4. Persist legal state transitions

Implemented a helper equivalent to:

```python
def transition_and_save(investigation_id, investigation, new_state):
    investigation.transition_to(new_state)
    save_investigation(investigation_id, investigation.state.value)
```

This preserves the important ordering:

```text
FSM validates transition
→ transition succeeds
→ new state is persisted
```

An illegal transition such as:

```text
EXECUTING → INVESTIGATING
```

was rejected by the FSM before the database was updated, leaving the persisted state unchanged.

### 5. Persist pending actions

A pending action was stored as data rather than executable code:

```text
request_id
investigation_id
tool name
arguments as JSON
```

Example:

```python
save_pending_action(
    "request-001",
    "investigation-001",
    "disable_user",
    {"user": "alice"}
)
```

`json.dumps()` serialized the argument dictionary into SQLite text, and `json.loads()` reconstructed it later.

### 6. Trusted tool registry

Executable Python function objects were intentionally not stored in SQLite.

Instead, the database stores only:

```text
"disable_user"
```

and trusted application code resolves that string through a registry:

```python
tool_registry = {
    "disable_user": disable_user
}
```

This acts like a function-reference table and also provides an execution allowlist.

The persisted action can then be reconstructed:

```text
action["tool"]
→ lookup in tool_registry
→ trusted Python function

action["args"]
→ restored dictionary
→ ** expands dictionary into keyword arguments
```

For example:

```python
function(**action["args"])
```

with:

```python
{"user": "alice"}
```

is effectively:

```python
disable_user(user="alice")
```

### 7. Explicit approval path

An important design correction occurred during the lab. The initial code loaded a pending action and executed it directly, implicitly assuming approval had already happened.

That was changed so execution lives inside an explicit approval function:

```text
pending action
→ approve_pending_action(request_id)
→ load pending action
→ verify tool is in trusted registry
→ restore investigation FSM
→ AWAITING_APPROVAL → EXECUTING
→ execute tool
→ persist outcome
→ consume pending action
```

This connects persistent state back to the approval boundary introduced in Lab 4.

### 8. Successful execution

For a successful action:

```text
AWAITING_APPROVAL
→ EXECUTING
→ tool succeeds
→ COMPLETED
→ delete pending action
```

The database then showed:

```text
investigation-001 → completed
request → no longer pending
```

### 9. Execution failure

A simulated failure was added for `fail-user`.

The execution path was wrapped in `try/except`:

```text
AWAITING_APPROVAL
→ EXECUTING
→ tool raises exception
→ BLOCKED
→ consume pending action
```

This prevented a failed process from leaving the persisted investigation incorrectly stuck in `EXECUTING`.

### 10. Rejection path

Implemented persistent rejection:

```text
AWAITING_APPROVAL
→ reject_pending_action(request_id)
→ BLOCKED
→ delete pending action
→ tool never executes
```

This completed both approval outcomes for the first-pass workflow.

---

## Questions and Answers

### Is the triple-quoted `CREATE TABLE` text a comment?

No. Triple quotes create a Python string. Inside `connection.execute(...)`, that string is passed to SQLite and executed as SQL. A standalone unused triple-quoted string may appear to behave like a block comment, but technically it is still a string literal. Real Python comments use `#`.

### What does `connection.commit()` do?

The SQL write occurs inside a transaction. `commit()` makes that transaction durable. Read-only `SELECT` operations do not require a commit.

### Should every request be saved in the database?

No. Persist state that must survive a process restart. A short-lived read-only request can remain in memory. Long-running investigations, pending approvals, important workflow status, and other resumable state should be durable.

### Why is `tool_registry` a dictionary?

The database stores a string tool name, while the running application needs a Python callable. A dictionary provides a direct mapping:

```text
"disable_user" → disable_user function
```

It is similar conceptually to a function-pointer/function-reference table and also acts as an allowlist.

### Where does `action["args"]` come from?

It originates from the arguments passed into `save_pending_action()`, is serialized with `json.dumps()`, stored in `args_json`, then reconstructed with `json.loads()` when the pending action is loaded.

### What does `function(**action["args"])` do?

`action["args"]` is a dictionary. `**` expands its key/value pairs into keyword arguments. For example:

```python
{"user": "alice"}
```

becomes:

```python
function(user="alice")
```

### Does learning `**kwargs` and storing functions in dictionaries expose a basic Python gap?

It exposes a Python-specific basic-to-intermediate language gap, not a general programming-fundamentals gap. The underlying concepts were quickly mapped to familiar ideas such as function pointers and argument passing.

### Is `action` effectively an object containing everything needed to execute the function?

Yes, with an important boundary: it contains the execution data—tool name and arguments—but not the trusted function implementation itself. Executable behavior comes from application code through the registry.

### Is `pending_actions` basically a queue of work waiting to execute?

Conceptually, yes. It contains actions that have not yet been consumed. Once an approved action is attempted, it should no longer remain pending. Success or failure belongs to workflow/action outcome state, not the pending queue.

### Does the execution block itself mean an action was approved?

Initially the lab implicitly assumed that. The design was corrected so that execution occurs only through `approve_pending_action(request_id)`. Approval is therefore the trigger for execution rather than an unstated assumption.

### Why delete a pending action on both success and failure?

Once approval is consumed and execution is attempted, the action is no longer pending. Leaving it in the pending table could permit unintended replay. A production system should normally preserve the attempt and result in an audit/history table rather than simply deleting all evidence.

### Does successful execution mean the entire investigation is complete?

Not necessarily. The current first-pass lab assumes one approval-required action per investigation, so successful execution transitions the investigation to `COMPLETED`.

A more realistic investigation may contain several actions:

```text
investigation-001
├── disable user
├── revoke sessions
└── isolate host
```

Completing one action should not automatically complete the whole investigation. A more mature design should separate **action status** from **investigation state** and allow the workflow controller to decide whether more work remains.

---

## Security / Reliability Implications

1. **Persist data, not executable objects.** Tool names and validated arguments can be durable; function implementations should come from trusted application code.
2. **Use an allowlisted registry.** A stored string should not be dynamically imported or executed without validation.
3. **Persistence must not bypass FSM rules.** Restore state, then use the same deterministic transition enforcement as the in-memory workflow.
4. **Consumed approvals should not be replayable.** Pending actions are removed after an execution attempt.
5. **Failure must update durable state.** Otherwise a crash or exception can leave the database reporting `EXECUTING` indefinitely.
6. **Database tampering matters.** A stronger design should revalidate persisted arguments before execution and protect database integrity/access.
7. **Deletion is not audit history.** Production systems should retain approval, rejection, execution result, actor identity, timestamps, and failure details.
8. **Separate database writes are not yet atomic as one workflow transaction.** A crash between state update and pending-action cleanup could create inconsistent durable state. Production code would use stronger transaction boundaries/idempotency controls.
9. **SQLite is a learning implementation.** Multi-instance workers, concurrency, distributed locking, and cloud durability are not addressed.

---

## Important Limitation

The lab still models approximately one pending action as the decisive action for one investigation. It does not yet implement:

- multiple actions per investigation;
- separate action lifecycle/state table;
- action history/audit log;
- atomic state + action transitions;
- idempotency keys/replay protection beyond deleting pending rows;
- multi-worker concurrency/locking;
- approval identity/timestamps;
- production database or cloud state store.

These are orchestration/persistence concerns for a later advanced pass rather than requirements for this first-pass lab.

---

## What Was Demonstrated vs Guided

The implementation was guided, so the score remains conservative. However, several useful design issues were identified during the work rather than simply accepted:

- approval was initially implicit and should be an explicit execution boundary;
- pending actions represent unconsumed work, not outcome history;
- successful execution of one action does not inherently mean an entire investigation is complete;
- function references and `**` argument expansion were mapped to existing programming concepts.

---

## Score Change

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Agent Memory / Persistent State | 1.5 | 3.0 | Implemented durable SQLite-backed investigation state and pending actions, FSM reconstruction, legal persisted transitions, trusted tool reconstruction, persistent approve/reject paths, success/failure handling, and restart recovery |

Other scores remain unchanged because this lab persisted existing FSM/tool/approval behavior but did not yet solve general multi-action orchestration, production database design, concurrency, audit history, or distributed recovery.
