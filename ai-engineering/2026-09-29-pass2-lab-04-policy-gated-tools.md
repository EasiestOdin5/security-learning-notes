# Pass 2 — Lab 4: Policy-Gated Tools

**Date completed:** September 29, 2026  
**Status:** Completed  
**Pass:** Pass 2 — guided design, increasingly independent implementation

---

## Goal

Extend the read-only tool workflow so the LLM may request a **state-changing action**, while deterministic Python policy prevents that action from executing until an explicit human approval step occurs.

Target architecture:

```text
Alert
  ↓
LLM investigates with read-only tools
  ↓
LLM requests disable_user("alice")
  ↓
Python validates request
  ↓
Policy check
  ├─ auto → execute immediately
  └─ approval_required → store pending action
                           ↓
                     approve / reject
                       ├─ approve → execute exact stored action
                       └─ reject  → never execute
```

The main principle is that **the model can request an action, but deterministic application code controls authorization and execution**.

---

## New State-Changing Tool

In `investigation_tools.py`:

```python
def disable_user(username: str):
    return {
        "username": username,
        "status": "disabled"
    }
```

Argument validation:

```python
class DisableUserArgs(BaseModel):
    username: str = Field(..., min_length=1)
```

The function itself is simple because this lab focuses on authorization workflow rather than integration with a real identity provider.

---

## LLM-Facing Tool Interface

A third tool definition was added to the existing OpenAI `tools` list:

```python
{
    "type": "function",
    "name": "disable_user",
    "description": "Disable user",
    "parameters": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "Username to disable"
            }
        },
        "required": ["username"],
        "additionalProperties": False
    },
    "strict": True
}
```

This creates the **LLM-facing interface** for `disable_user`, but does not itself authorize execution.

---

## Tool Policy

A separate deterministic policy mapping was introduced:

```python
tool_policy = {
    "get_ip_reputation": "auto",
    "get_user_activity": "auto",
    "disable_user": "approval_required"
}
```

This separates two questions:

1. Is this a known tool?
2. If known, may it execute automatically?

That means the dispatch flow became:

```text
known tool?
  ↓
validate arguments
  ↓
lookup tool_policy
  ├─ auto
  └─ approval_required
```

---

## Auto vs Approval-Required Branch

After Pydantic argument validation and conversion to JSON-compatible values:

```python
policy = tool_policy[result["name"]]
```

For `auto` tools:

```python
tool_result = tool_function(**validated_args)
```

The result is immediately packaged as `function_call_output`.

For `approval_required` tools:

- the function is **not** executed;
- a UUID request ID is generated;
- the exact pending action is stored.

---

## Pending Action Store

A global in-memory store was created:

```python
pending_actions = {}
```

Each pending action is keyed by a generated UUID:

```python
request_id = str(uuid.uuid4())

pending_action = {
    "name": result["name"],
    "arguments": validated_args,
    "call_id": result["call_id"],
    "status": "waiting_for_approval",
    "request_id": request_id
}

pending_actions[request_id] = pending_action
```

The request ID becomes the lookup key used by later approval/rejection endpoints.

Important design point: the function object itself is not stored. The tool name is stored, and the executable function is looked up again through `tool_functions`. This keeps the pending record simple and serializable.

---

## Approval Endpoint

A `POST /approve` endpoint was added.

Its logic:

1. verify `request_id` exists;
2. retrieve the stored pending action;
3. require status `waiting_for_approval`;
4. look up the exact function by stored tool name;
5. execute it with the exact stored arguments;
6. mark status `executed`;
7. return the execution result.

Core execution pattern:

```python
tool_name = pending_action["name"]
tool_function, args_model = tool_functions[tool_name]
tool_arguments = pending_action["arguments"]

result = tool_function(**tool_arguments)
pending_actions[request_id]["status"] = "executed"
```

Verified response:

```json
{
  "request_id": "a2de8534-3140-42f1-9604-bcd2799b4787",
  "status": "executed",
  "result": {
    "username": "alice",
    "status": "disabled"
  }
}
```

---

## Rejection Endpoint

A `POST /reject` endpoint was added.

Its behavior:

- find the exact pending action;
- require `waiting_for_approval`;
- change status to `rejected`;
- do **not** call the stored tool.

Verified response:

```json
{
  "request_id": "9fbef9ab-1d22-4ee5-8ea7-3b74b500096e",
  "status": "rejected"
}
```

This demonstrated the deterministic branch:

```text
waiting_for_approval
  ├─ approve → executed
  └─ reject  → rejected
```

---

## HTTP Error Cleanup

Initially, invalid IDs and invalid statuses only printed messages.

This was changed to explicit FastAPI errors.

For an unknown request ID:

```python
raise fastapi.HTTPException(
    status_code=404,
    detail="request_id not found"
)
```

For an action no longer waiting for approval:

```python
raise fastapi.HTTPException(
    status_code=409,
    detail=f"action already {status}"
)
```

Observed 404 response:

```json
{
  "detail": "request_id not found"
}
```

Swagger displayed the response as **Undocumented** because no explicit 404 response schema was declared in the route decorator. The actual HTTP behavior was still correct.

---

## Orchestration Bug Found During Testing

The first Lab 4 design reused the Lab 3 final call:

```python
responses.parse(..., text_format=InvestigationAssessment)
```

That caused the second model turn to jump directly to a final assessment instead of remaining tool-enabled.

The model could recommend:

```text
Request immediate disabling of Alice's account.
```

but could not emit an actual:

```text
function_call: disable_user(...)
```

This was identified as an orchestration error in the lab design.

The correction was:

```text
response1 = create(...)   # read-only tool selection
response2 = create(...)   # tool-enabled continuation; may request disable_user
final     = parse(...)    # only after tool calling is finished
```

The second call was changed to:

```python
response2 = client.responses.create(
    model="gpt-5.6-luna",
    previous_response_id=response.id,
    input=results_for_llm,
    tools=tools
)
```

The same tool-processing logic was then applied to `response2.output`.

---

## Tool Use Is Optional Unless Constrained

After the corrected tool-enabled second call, the model still sometimes returned a normal assistant message rather than a `disable_user` function call.

This clarified:

```text
tools=tools
→ model may call a tool
→ model may also answer directly
```

A more severe test alert was used so the model would be more likely to request `disable_user`.

The resulting flow successfully produced:

```text
ALLOWED: disable_user
Validated arguments: username='alice'
PENDING APPROVAL: <uuid>
```

The lab did not permanently force `disable_user` with `tool_choice`; the severe test case was sufficient to demonstrate the approval path.

---

## Investigation Response Cleanup

The `/investigate` response was updated so pending actions were surfaced through the API rather than only printed to the console.

Example final response shape:

```json
{
  "tools_requests": [
    {
      "name": "get_user_activity",
      "arguments": {
        "username": "alice"
      },
      "call_id": "call_..."
    },
    {
      "name": "get_ip_reputation",
      "arguments": {
        "ip": "8.8.8.8"
      },
      "call_id": "call_..."
    },
    {
      "name": "disable_user",
      "arguments": {
        "username": "alice"
      },
      "call_id": "call_..."
    }
  ],
  "pending_actions": [
    {
      "name": "disable_user",
      "arguments": {
        "username": "alice"
      },
      "call_id": "call_...",
      "status": "waiting_for_approval",
      "request_id": "9ae2e68b-2909-4e92-aa0a-94d999e65e7a"
    }
  ]
}
```

This clearly separates:

- what the model requested;
- what deterministic policy held for approval.

---

## Questions and Answers

### Does adding `disable_user` to the tool list mean it executes automatically?

No. The `tools` list only exposes the interface to the LLM. Python policy still controls whether execution is automatic or approval-gated.

### Where should the policy check happen?

After the tool name is recognized and arguments are validated, but **before** calling the actual Python function.

### Should `waiting_for_approval` be stored in `tool_result`?

No. `tool_result` should represent a function that actually executed. A separate `pending_action` object should represent an action that has not yet run.

### Why use a UUID for each pending action?

The UUID gives each pending request a unique lookup key, allowing `/approve` or `/reject` to target one exact stored action.

### Is the request ID by itself authorization?

No. In a production system, the application must also verify that the approver is authenticated and authorized. The UUID is an identifier, not a permission.

### Why not store the function object in `pending_actions`?

Storing the tool name keeps the pending record simpler and easier to serialize. On approval, the application re-resolves the real function through `tool_functions`.

### Can `POST /approve` accept the request ID in the body instead of the URL?

Yes. Both `POST /approve/{request_id}` and `POST /approve` with a request body/query parameter are valid API designs. The lab used `POST /approve` with `request_id` supplied as a FastAPI parameter.

### Do invalid IDs require `try/except`?

No. A missing ID or invalid state is expected control flow, so direct checks plus `HTTPException` are cleaner.

### Why use 404 for unknown request ID?

The referenced resource/action does not exist.

### Why use 409 for an already executed or rejected action?

The request conflicts with the action's current state. For example, an executed action should not be executed again.

### Why did the second model initially not call `disable_user`?

Because it had been converted into a final structured-output step. Even after restoring tools, tool use remained optional, so the model could still answer directly unless it decided the action was needed.

### Why was the second call changed back to `responses.create()`?

That intermediate turn needed raw `function_call` items. Final structured parsing should occur only after the tool loop is finished.

### Why duplicate the response-processing loop for `response2`?

For the lab, duplication made the second turn explicit and easier to understand. A larger implementation should refactor this into a reusable tool-processing helper or bounded loop.

### Why return pending actions from `/investigate`?

A caller should not need access to application console logs to obtain a request ID. Returning pending actions makes the approval workflow usable through the API itself.

### Why not return the entire global `pending_actions` dictionary?

That is possible, but a list of relevant pending actions is cleaner and avoids exposing unrelated global state. Ideally, only actions created by the current investigation should be returned.

---

## What Was Independent vs Guided

### Independent / increasingly independent

- implemented `disable_user`;
- added `DisableUserArgs`;
- wrote the LLM-facing `disable_user` tool definition;
- understood that the policy check belongs before function execution;
- implemented the `auto` vs `approval_required` branch;
- created UUID-based pending actions;
- stored tool name, arguments, call ID, status, and request ID;
- implemented `/approve` lookup and execution logic;
- implemented `/reject` without execution;
- added state checks preventing repeated execution/rejection;
- added 404 and 409 HTTP errors;
- surfaced pending actions from `/investigate`;
- tested approval, rejection, and missing-ID behavior.

### Guided / corrected

- suggestion to use a policy mapping;
- suggestion to use a UUID-keyed pending-action store;
- approval/rejection endpoint sequence;
- recommendation not to store raw function objects;
- HTTP status-code choices;
- lab orchestration correction from immediate `parse()` to another tool-enabled `create()`;
- second-response tool-processing pattern;
- discussion of optional model tool use and stronger test input.

A notable point in this lab is that the user identified the orchestration design flaw: the second call had been turned into a final parse step too early, preventing `disable_user` from being requested.

---

## Remaining Limitations

The core policy-gated workflow is complete, but production concerns remain:

- `pending_actions` is in-memory only and disappears on restart;
- no authentication/authorization of approvers;
- no audit log of who approved or rejected;
- no expiration/TTL for stale pending actions;
- duplicated tool-processing code should become a reusable bounded loop;
- the action state is still a string rather than a formal FSM;
- no concurrency/locking protection around pending-action state;
- no durable transaction semantics around approval/execution;
- the final structured `InvestigationAssessment` step should be reintroduced only after the tool loop terminates.

These are intentionally deferred to later Pass 2 labs.

---

## Conservative Score Changes

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Tool / Function Calling | 4.25 | 4.5 | Rebuilt a state-changing tool request path and connected model-selected action requests to an approval-gated execution flow |
| Agent Orchestration | 3.25 | 3.5 | Implemented a second tool-enabled model turn and corrected the premature-final-answer orchestration mistake |
| Deterministic Gates / Policy Controls | 5.75 | 6.25 | Independently implemented auto vs approval-required policy, UUID-scoped pending actions, exact-action approval/rejection, status checks, and HTTP conflict/not-found handling |
| Agent Security / Threat Modeling | 5.25 | 5.5 | Implemented an actual human-approval boundary for a high-impact state-changing action rather than only discussing the control |

No State Machine score increase: the workflow uses status strings but does not yet implement a formal FSM. No persistence score increase: pending actions remain in memory.

---

## Main Takeaway

The application now distinguishes **model intent** from **execution authority**:

```text
LLM: "disable alice"
        ↓
Python: validate request
        ↓
Policy: approval required
        ↓
Store exact pending action
        ↓
Human decision
  ├─ approve → execute
  └─ reject  → never execute
```

This is a core safety boundary for agentic applications: a model can recommend or request a high-impact action without being trusted to authorize that action itself.
