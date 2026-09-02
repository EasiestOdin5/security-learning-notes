# AI Engineering Lab 4 — Policy-Gated Tools

**Date:** September 2, 2026  
**Status:** Completed  
**Primary objective:** Separate LLM intent from deterministic authorization for state-changing tools.

---

## Goal

Extend the read-only tool-calling work from Lab 3 so the model can *request* a state-changing action without being able to authorize or execute that action by itself.

Target pattern:

```text
LLM requests action
        ↓
Python validates tool + arguments
        ↓
Python checks policy metadata
        ↓
State-changing action requires approval
        ↓
Exact action stored as pending
        ↓
Human/workflow approves or rejects
        ↓
APPROVE → execute once
REJECT  → remove without execution
```

The main security rule is:

> The LLM may propose an action, but authorization and execution remain deterministic and external to the model.

---

## Starting Point from Lab 3

The existing tool registry stored tuples:

```python
tool_functions = {
    "get_ip_reputation": (get_ip_reputation, IPReputationArgs),
    "get_user_activity": (get_user_activity, UserActivityArgs),
}
```

This was sufficient when each tool only needed a function and argument validator.

Lab 4 introduced policy metadata, so the registry was changed from tuples to dictionaries:

```python
tool_functions = {
    "get_ip_reputation": {
        "function": get_ip_reputation,
        "args_model": IPReputationArgs,
        "requires_approval": False
    },
    "get_user_activity": {
        "function": get_user_activity,
        "args_model": UserActivityArgs,
        "requires_approval": False
    }
}
```

Why use dictionaries instead of tuples?

- Named fields are easier to read than positional indexes.
- Policy metadata can be added without relying on tuple position.
- The structure can later grow to include fields such as risk level, allowed roles, read-only/state-changing classification, or approval requirements.

The executor now retrieves named configuration values:

```python
tool_config = tool_functions[item.name]

function = tool_config["function"]
argument_model = tool_config["args_model"]
requires_approval = tool_config["requires_approval"]
```

---

## State-Changing Mock Tool

Added to `main.py`:

```python
def disable_user(user: str):
    return {
        "user": user,
        "status": "disabled"
    }
```

The function is intentionally a mock. The purpose of the lab is authorization flow, not integration with a real identity provider.

Argument validation model:

```python
class DisableUserArgs(BaseModel):
    user: str
```

Policy-aware registry entry:

```python
"disable_user": {
    "function": disable_user,
    "args_model": DisableUserArgs,
    "requires_approval": True
}
```

The important distinction is that `disable_user` is executable Python code, but `requires_approval=True` prevents direct automatic execution.

---

## Exposing the Tool to the LLM

The state-changing action was also added to `tools = []` so the model is allowed to *request* it:

```python
{
    "type": "function",
    "name": "disable_user",
    "description": "Disable a user account.",
    "parameters": {
        "type": "object",
        "properties": {
            "user": {
                "type": "string",
                "description": "Username to disable"
            }
        },
        "required": ["user"],
        "additionalProperties": False
    },
    "strict": True
}
```

This does **not** authorize execution. It only tells the model that the action exists and what arguments it takes.

---

## First Approval Gate

The initial approval gate was:

```python
if requires_approval:
    print("PENDING APPROVAL:", item.name, validated_args)
    continue

result = function(**validated_args)
```

Test prompt:

```python
input="Disable user alice."
```

Observed result:

```text
user='alice'
PENDING APPROVAL: disable_user {'user': 'alice'}
```

No tool result appeared, proving `disable_user()` did not execute.

---

## Simple Approval Switch

A first explicit approval mechanism used a deterministic application-side dictionary:

```python
approved_actions = {
    "disable_user": False
}
```

Gate:

```python
if requires_approval and not approved_actions.get(item.name, False):
    print("PENDING APPROVAL:", item.name, validated_args)
    continue
```

Question: What does `item.name` refer to?

Answer: It is the tool name supplied by the model in the returned `function_call`. For a request to disable Alice, the model might return:

```text
item.name == "disable_user"
```

The model chooses what to request, so `item.name` is untrusted model output. Python still validates the name against `tool_functions` before using it.

Question: Is `approved_actions` basically an auto-approve switch?

Answer: In this simplified lab version, yes. It is deterministic application state. A real application would obtain approval from a human, role/permission check, policy engine, or workflow state rather than a hard-coded boolean.

With:

```python
approved_actions = {
    "disable_user": True
}
```

Observed result:

```text
user='alice'
Tool result: {'user': 'alice', 'status': 'disabled'}
User `alice` has been disabled.
```

This proved that only application-side approval unlocked execution.

---

## Why Tool-Level Approval Was Too Broad

A global entry such as:

```python
approved_actions["disable_user"] = True
```

could unintentionally authorize every future `disable_user` call.

The approval was therefore narrowed to action + arguments:

```python
approved_actions = {
    ("disable_user", "alice"): True
}
```

Gate:

```python
approval_key = (
    item.name,
    validated_args.get("user")
)

if requires_approval and not approved_actions.get(approval_key, False):
    print("PENDING APPROVAL:", item.name, validated_args)
    continue
```

Test results:

```text
user='alice'
Tool result: {'user': 'alice', 'status': 'disabled'}
User `alice` has been disabled.

user='bob'
PENDING APPROVAL: disable_user {'user': 'bob'}
```

This demonstrated that approving `disable_user("alice")` did not authorize `disable_user("bob")`.

---

## One-Time Approval

An approved action can be consumed after execution:

```python
if requires_approval:
    if not approved_actions.get(approval_key, False):
        print("PENDING APPROVAL:", item.name, validated_args)
        continue

    approved_actions.pop(approval_key)
```

Important observation: restarting a Python script recreates an in-memory approval dictionary, so one-time approval must be tested within the same running process or with external persistent state.

Two identical requests were therefore executed in one Python process.

Observed result:

```text
user='alice'
Tool result: {'user': 'alice', 'status': 'disabled'}
User `alice` has been disabled.
user='alice'
PENDING APPROVAL: disable_user {'user': 'alice'}
```

The first execution consumed the approval; the second request required a new approval.

---

## Pending Action Model

The lab then moved away from pre-populating an approval switch. Instead, the exact model-requested action was captured first:

```python
pending_actions = {}
```

Pending action storage:

```python
if requires_approval:
    approval_key = (
        item.name,
        validated_args.get("user")
    )

    pending_actions[approval_key] = {
        "function": function,
        "args": validated_args
    }

    print("PENDING APPROVAL:", approval_key)
    continue
```

This changed the workflow to:

```text
LLM requests action
→ Python stores exact request
→ action does not execute
→ user/workflow approves stored request
→ Python executes stored request directly
```

The LLM is not asked to recreate the action after approval.

---

## Approve and Reject Functions

Approval function:

```python
def approve_action(approval_key):
    if approval_key not in pending_actions:
        print("NO PENDING ACTION")
        return

    action = pending_actions.pop(approval_key)

    result = action["function"](**action["args"])

    print("APPROVED AND EXECUTED:", result)
```

Rejection function:

```python
def reject_action(approval_key):
    if approval_key not in pending_actions:
        print("NO PENDING ACTION")
        return

    pending_actions.pop(approval_key)

    print("REJECTED:", approval_key)
```

Approval test:

```text
user='alice'
PENDING APPROVAL: ('disable_user', 'alice')
Pending: {('disable_user', 'alice'): {...}}
APPROVED AND EXECUTED: {'user': 'alice', 'status': 'disabled'}
Pending after approval: {}
```

Rejection test:

```text
user='bob'
PENDING APPROVAL: ('disable_user', 'bob')
Pending: {('disable_user', 'bob'): {...}}
REJECTED: ('disable_user', 'bob')
Pending after rejection: {}
```

The rejected request was removed without calling `disable_user()`.

---

## Unique Request IDs

Using `(tool_name, user)` is still ambiguous when the same action can be requested multiple times. Pending actions were therefore changed to use UUID request IDs.

Added:

```python
import uuid
```

Storage:

```python
if requires_approval:
    request_id = str(uuid.uuid4())

    pending_actions[request_id] = {
        "tool": item.name,
        "function": function,
        "args": validated_args
    }

    print(
        "PENDING APPROVAL:",
        request_id,
        item.name,
        validated_args
    )
    continue
```

Approval or rejection now refers to the UUID rather than reconstructing the action key.

Initial rejection test failed with:

```text
NO PENDING ACTION
```

because the test was still passing the old tuple key. It was corrected by retrieving the generated UUID:

```python
request_id = next(iter(pending_actions))
reject_action(request_id)
```

Successful rejection:

```text
user='bob'
PENDING APPROVAL: aed616aa-d32b-4c93-aa65-7008270ae315 disable_user {'user': 'bob'}
Pending: {'aed616aa-d32b-4c93-aa65-7008270ae315': {...}}
REJECTED: aed616aa-d32b-4c93-aa65-7008270ae315
Pending after rejection: {}
```

Successful approval:

```text
user='alice'
PENDING APPROVAL: fe5ae23e-bc34-4cd1-91e3-9aa102572f28 disable_user {'user': 'alice'}
Pending: {'fe5ae23e-bc34-4cd1-91e3-9aa102572f28': {...}}
APPROVED AND EXECUTED: {'user': 'alice', 'status': 'disabled'}
Pending after approval: {}
```

---

## Question: Why Use a Direct Command When the Real Input Is an Alert?

The direct prompt:

```text
Disable user alice.
```

was used only to deterministically exercise the state-changing tool path.

The intended real architecture still begins with an alert, for example:

```text
Security alert: user alice had 25 failed login attempts,
followed by a successful login from a known malicious IP.
Investigate and take appropriate action.
```

The model might investigate first, then eventually propose a state-changing action. The approval layer must remain the same regardless of why the model requested that action.

---

## Multi-Turn Detour and Scope Correction

A realistic alert test caused the model to request `get_user_activity` rather than immediately request `disable_user`:

```text
user='alice'
Tool result: {'user': 'alice', 'failed_logins': 7, 'successful_logins': 1, 'last_source_ip': '8.8.8.8'}
```

A multi-turn `while True` control loop was briefly introduced so the model could receive investigation results and make another decision.

This exposed an important behavior: the model repeatedly requested the same tool:

```text
user='alice'
Tool result: {...}

user='alice'
Tool result: {...}

user='alice'
Tool result: {...}
```

A duplicate-call blocker and `max_steps` limit were temporarily introduced. The model continued requesting the same tool and produced repeated blocked calls.

The user identified an important design concern: blocking one model-selected action and automatically giving the model another decision turn can indirectly encourage the model to choose some other action. That may be unsafe for security-sensitive agents.

Another important question was raised: repeated calls are not always wrong. A deobfuscation workflow may legitimately call the same transformation tool multiple times while the input changes layer by layer.

Conclusion:

- A universal "never repeat tools" rule is too simplistic.
- Repeat policy may need to be tool-specific and progress-aware.
- Hard step bounds are important, but they are orchestration/state-machine concerns.
- The growing loop logic was outside the intended Lab 4 scope.

The lab was deliberately simplified again by removing:

- `while True`
- `executed_calls`
- duplicate-call blocking
- `max_steps`
- per-tool repeat policy experiments

These concerns are deferred to later state-machine/orchestration and bounded-retry labs.

This scope correction was intentional rather than treating additional complexity as automatically better.

---

## Final Simplified `run_request()` Design

The completed Lab 4 request path is single-pass and policy-focused:

```python
def run_request(prompt):

    response = client.responses.create(
        model="gpt-5.6-luna",
        tools=tools,
        input=prompt
    )

    tool_outputs = []

    for item in response.output:

        if item.type != "function_call":
            continue

        if item.name not in tool_functions:
            print("BLOCKED: tool_not_allowed")
            continue

        tool_config = tool_functions[item.name]

        function = tool_config["function"]
        argument_model = tool_config["args_model"]
        requires_approval = tool_config["requires_approval"]

        try:
            args = argument_model.model_validate_json(item.arguments)
            print(args)

        except ValidationError as e:
            print("BLOCKED: invalid_arguments")
            print(e)
            continue

        validated_args = args.model_dump(mode="json")

        try:
            if item.name == "get_ip_reputation":
                validate_ip_policy(validated_args["ip"])

        except ValueError as e:
            print("BLOCKED:", e)
            continue

        if requires_approval:

            request_id = str(uuid.uuid4())

            pending_actions[request_id] = {
                "tool": item.name,
                "function": function,
                "args": validated_args
            }

            print(
                "PENDING APPROVAL:",
                request_id,
                item.name,
                validated_args
            )

            continue

        result = function(**validated_args)

        print("Tool result:", result)

        tool_outputs.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(result)
        })

    if tool_outputs:

        final_response = client.responses.create(
            model="gpt-5.6-luna",
            previous_response_id=response.id,
            tools=tools,
            input=tool_outputs
        )

        print(final_response.output_text)
```

---

## Final Lab 4 Tests

### Approve Alice

```text
user='alice'
PENDING APPROVAL: 13609b92-34a8-4584-becc-7512ac9cd45e disable_user {'user': 'alice'}
Pending: {'13609b92-34a8-4584-becc-7512ac9cd45e': {...}}
APPROVED AND EXECUTED: {'user': 'alice', 'status': 'disabled'}
Pending after approval: {}
```

### Reject Bob

```text
user='bob'
PENDING APPROVAL: a577307b-2d01-4ed7-aab6-684891346ba9 disable_user {'user': 'bob'}
Pending: {'a577307b-2d01-4ed7-aab6-684891346ba9': {...}}
REJECTED: a577307b-2d01-4ed7-aab6-684891346ba9
Pending after rejection: {}
```

Both tests passed.

---

## Questions and Answers

### Why change the tool registry from tuples to dictionaries?

Policy-gated tools need more metadata than just `(function, argument_model)`. Named dictionary fields remain readable and extensible as policy data grows.

### Does `item.name` definitely mean `disable_user`?

Only if that is what the model requested in that `function_call`. The model controls the requested name, so Python must treat it as untrusted and check it against the deterministic registry.

### What does `.get("disable_user", False)` mean?

It returns the stored value for `"disable_user"`; if the key does not exist, it returns the supplied fallback `False`.

### Is the approval dictionary an auto-approve switch?

The first version effectively was. It was useful for demonstrating the concept but was too coarse for a real system.

### Would a real system temporarily set approval to `True` after the user approves?

Conceptually yes, but approval should be tied to a specific action/request rather than a global tool switch.

### Why tie approval to tool + arguments?

Approving `disable_user("alice")` should not automatically authorize `disable_user("bob")`.

### Why move from tool + arguments to a UUID?

The same tool/arguments can be requested multiple times. A unique request ID identifies one exact pending action instance.

### Why does `approve_action()` execute the stored function directly?

After the model has proposed the action and a human approves that exact request, there is no need to ask the model to recreate it. Python executes the already validated stored action.

### Why is rejection important?

Human approval is not merely an execution delay. A pending action needs an explicit terminal path where it is removed without execution.

### Was the repeated-tool loop part of Lab 4?

No. It emerged while testing a realistic alert. It exposed useful orchestration questions, but continuing to add loop controls would have bloated the policy-gating lab. The issue is intentionally deferred.

### Can repeated tool calls ever be legitimate?

Yes. Multi-layer deobfuscation is one example where the same tool may need repeated calls while the input changes. Repeat controls therefore need more context than a blanket prohibition.

---

## Security Lessons

1. **Tool exposure is not authorization.** A tool can be visible to the model while Python still blocks execution.
2. **Model intent is untrusted.** Tool name and arguments originate from a nondeterministic model and must pass deterministic checks.
3. **Read and write capabilities should have different policies.** Read-only investigation tools can often execute automatically; state-changing actions may require approval.
4. **Approval must be scoped.** A global `disable_user=True` approval is dangerously broad.
5. **Approval should identify an exact action instance.** UUID request IDs avoid ambiguity between repeated requests.
6. **Approval should be consumable.** An authorization decision should not silently become permanent permission for future actions.
7. **Rejection is a first-class workflow outcome.** A denied action must remain unexecuted.
8. **Hard policy should remain outside the LLM.** The model can explain a decision, but it should not be able to reinterpret authorization.
9. **More agent autonomy is not automatically better.** Multi-turn loops create additional control and safety requirements.
10. **Scope matters.** Loop detection, progress tracking, iteration limits, and retry policies should be designed deliberately in orchestration/state-machine labs rather than accumulated ad hoc inside an authorization lab.

---

## What Was Demonstrated Independently

The user correctly identified several architectural issues during the lab rather than only following implementation steps:

- Recognized that a global approval switch could act as auto-approval.
- Asked how the application knows what `item.name` means and recognized that the LLM decides the request.
- Identified that one-time approval cannot be meaningfully tested by restarting a script that recreates state.
- Distinguished direct command prompts used for testing from the intended alert-driven workflow.
- Identified that the multi-turn loop was becoming unsafe/bloated.
- Noted that blocking one LLM action and forcing another model turn could create undesirable alternative actions.
- Identified legitimate repeat-tool scenarios such as multi-layer deobfuscation.
- Challenged the expanding lab scope and prompted a cleaner separation between policy gating and later orchestration work.

---

## Completion Criteria

Lab 4 is complete because the implementation demonstrated:

- a state-changing tool exposed to the model;
- deterministic tool and argument validation retained from Lab 3;
- policy metadata distinguishing approval-required actions;
- prevention of automatic state-changing execution;
- pending-action storage;
- unique request IDs;
- explicit approval and rejection paths;
- execution only after approval;
- removal of the pending action after approval/rejection;
- successful approve and reject tests;
- recognition and deliberate deferral of multi-turn orchestration concerns.

The next lab should formalize workflow state rather than adding more ad hoc control flags.