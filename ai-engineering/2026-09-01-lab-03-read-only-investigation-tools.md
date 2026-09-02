# AI Engineering Lab 3 — Read-Only Investigation Tools

**Date:** September 1, 2026  
**Status:** Completed  
**Focus:** OpenAI function/tool calling, deterministic execution control, argument validation, policy gates, and evidence-grounded investigation

---

## Goal

Build the first tool-using investigation loop where the model can decide which read-only evidence it needs, while Python remains responsible for whether a requested tool is actually allowed to execute.

Target control flow:

```text
user investigation request
        ↓
LLM sees approved tool descriptions
        ↓
LLM emits structured function call(s)
        ↓
Python checks execution allowlist
        ↓
Python validates tool arguments
        ↓
Python applies deterministic policy
        ↓
read-only function executes
        ↓
function_call_output returned to LLM
        ↓
LLM summarizes the evidence
```

The central security principle is that **the model may request an action, but application code decides whether it executes**.

---

## Mock Read-Only Tools

The lab used local mock functions so the model/tool control loop could be inspected without depending on an external security service.

```python
def get_ip_reputation(ip: str):
    return {
        "ip": ip,
        "reputation": "suspicious",
        "score": 82
    }


def get_user_activity(user: str):
    if user == "bob":
        return {
            "user": user,
            "failed_logins": 0,
            "successful_logins": 1,
            "last_source_ip": None
        }

    return {
        "user": user,
        "failed_logins": 7,
        "successful_logins": 1,
        "last_source_ip": "8.8.8.8"
    }
```

These functions are application-side implementations. Merely defining them does **not** make the model aware that they exist.

---

## Exposing Tools to the Model

The model-facing tool definitions were supplied through the Responses API request:

```python
tools = [
    {
        "type": "function",
        "name": "get_ip_reputation",
        "description": "Look up the security reputation of an IP address.",
        "parameters": {
            "type": "object",
            "properties": {
                "ip": {
                    "type": "string",
                    "description": "IPv4 or IPv6 address to investigate"
                }
            },
            "required": ["ip"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "get_user_activity",
        "description": "Look up recent authentication activity for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "string",
                    "description": "Username to investigate"
                }
            },
            "required": ["user"],
            "additionalProperties": False
        },
        "strict": True
    }
]
```

The tool schema is the **model-facing contract**. The Python function is the **real implementation**.

---

## First Tool Request

Initial request:

```python
response = client.responses.create(
    model="gpt-5.6-luna",
    tools=tools,
    input="Investigate suspicious activity from IP 8.8.8.8."
)
```

The model returned a `ResponseFunctionToolCall` requesting:

```text
get_ip_reputation {"ip":"8.8.8.8"}
```

Important observation: printing `response.output` only proves the model **requested** the tool. It does not execute Python automatically.

---

## Executing the Requested Tool

The first explicit executor inspected the model response and called the matching Python function:

```python
for item in response.output:
    if item.type == "function_call":
        args = json.loads(item.arguments)

        if item.name == "get_ip_reputation":
            result = get_ip_reputation(**args)
            print(result)
```

Result:

```text
{'ip': '8.8.8.8', 'reputation': 'suspicious', 'score': 82}
```

---

## Returning Tool Output to the Model

The result was converted into `function_call_output` and associated with the original call using `call_id`:

```python
tool_output = {
    "type": "function_call_output",
    "call_id": item.call_id,
    "output": json.dumps(result)
}

final_response = client.responses.create(
    model="gpt-5.6-luna",
    previous_response_id=response.id,
    input=[tool_output]
)
```

`call_id` identifies the exact tool request that the result answers. `previous_response_id` continues the same model interaction.

The model then produced a natural-language investigation summary from the returned tool evidence.

---

## Grounding Observation

The IP reputation tool returned only:

```json
{
  "ip": "8.8.8.8",
  "reputation": "suspicious",
  "score": 82
}
```

The model also mentioned that `8.8.8.8` is Google Public DNS and generated security recommendations. Those details were **not returned by the tool**.

This demonstrated an important distinction:

```text
tool evidence ≠ everything in the model's final answer
```

A model can combine tool evidence with pretrained knowledge and inference. Later agent designs therefore need explicit evidence attribution and evaluation rather than assuming all final prose came directly from tools.

---

## Multiple Tools

A second function was exposed:

```python
def get_user_activity(user: str):
    return {
        "user": user,
        "failed_logins": 7,
        "successful_logins": 1,
        "last_source_ip": "8.8.8.8"
    }
```

Request:

```text
Investigate suspicious login activity for user alice from IP 8.8.8.8.
```

The model independently requested both tools:

```text
get_user_activity {"user":"alice"}
get_ip_reputation {"ip":"8.8.8.8"}
```

This demonstrated model-selected multi-tool evidence collection.

---

## Dynamic Tool Registry

Hard-coded `if item.name == ...` dispatch was replaced with a registry:

```python
tool_functions = {
    "get_ip_reputation": get_ip_reputation,
    "get_user_activity": get_user_activity,
}
```

Execution became:

```python
if item.name in tool_functions:
    result = tool_functions[item.name](**args)
```

The registry also became an execution **allowlist**: only functions explicitly present in application code can execute.

---

## Collecting Multiple Tool Outputs

Tool outputs were accumulated and returned to the model together:

```python
tool_outputs = []

for item in response.output:
    if item.type == "function_call":
        args = json.loads(item.arguments)

        if item.name in tool_functions:
            result = tool_functions[item.name](**args)

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result)
            })
```

Then:

```python
final_response = client.responses.create(
    model="gpt-5.6-luna",
    previous_response_id=response.id,
    tools=tools,
    input=tool_outputs
)
```

The model correlated the authentication activity with the IP reputation and produced one investigation summary.

---

## Troubleshooting: `json.dump` vs `json.dumps`

An early version used:

```python
json.dump(result)
```

and failed with:

```text
TypeError: dump() missing 1 required positional argument: 'fp'
```

Reason:

- `json.dump(...)` serializes JSON **to a file object**.
- `json.dumps(...)` serializes JSON **to a string**.

`function_call_output["output"]` needed a string, so `json.dumps(result)` was correct.

---

## Deterministic Tool Allowlist

The executor was changed so an unknown or unauthorized requested tool could not run:

```python
if item.name not in tool_functions:
    tool_outputs.append({
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": json.dumps({
            "error": "tool_not_allowed"
        })
    })
    continue
```

A temporary model-facing tool named `delete_user` was deliberately exposed, but no implementation was placed in the execution registry.

Request:

```text
Delete user alice.
```

The model requested the tool, but Python blocked execution because `delete_user` was absent from `tool_functions`.

The model later summarized the result as:

```text
I couldn’t delete user alice because the account-deletion tool is not authorized.
```

The security decision was made by Python. The model only explained the returned error.

---

## Hard Denial vs Returning Denial to the Model

Question: should a hard authorization denial be passed back to the LLM, or should execution stop immediately?

Answer: for a terminal security decision, stopping in deterministic Python is usually safer. A pattern such as:

```json
{
  "status": "blocked",
  "reason": "tool_not_allowed"
}
```

can be returned directly without asking the model to reinterpret the denial.

Returning the denial to the model is useful only when a natural-language explanation or explicitly permitted recovery step is wanted.

Security rule:

```text
LLM requests → Python policy decides → hard denial remains hard denial
```

A later nondeterministic model response must never be able to convert a denied action into an authorized one.

---

## Tool Argument Validation

The registry was expanded to associate each function with a Pydantic model:

```python
from pydantic import BaseModel, IPvAnyAddress, ValidationError


class IPReputationArgs(BaseModel):
    ip: IPvAnyAddress


class UserActivityArgs(BaseModel):
    user: str


tool_functions = {
    "get_ip_reputation": (
        get_ip_reputation,
        IPReputationArgs
    ),
    "get_user_activity": (
        get_user_activity,
        UserActivityArgs
    ),
}
```

Because registry values are now tuples, the previous call:

```python
result = tool_functions[item.name](**args)
```

is no longer valid. The tuple must first be unpacked:

```python
function, argument_model = tool_functions[item.name]
```

Then the model-provided JSON arguments are independently validated:

```python
try:
    args = argument_model.model_validate_json(item.arguments)
except ValidationError as e:
    print("BLOCKED: invalid_arguments")
    print(e)
    continue

validated_args = args.model_dump(mode="json")
result = function(**validated_args)
```

This establishes:

```text
tool allowed ≠ arguments automatically trusted
```

---

## Invalid-IP Tests

Direct validation test:

```python
try:
    args = IPReputationArgs.model_validate_json('{"ip":"not-an-ip"}')
except ValidationError as e:
    print("BLOCKED: invalid_arguments")
```

Observed:

```text
BLOCKED: invalid_arguments
value is not a valid IPv4 or IPv6 address
```

An end-to-end model request using:

```text
30.300.30.40
```

caused the model to request the tool, after which Pydantic rejected the invalid address before function execution.

A more obviously invalid input:

```text
300.300.300.40
```

produced no tool request. Inspection of `response.output` showed that the model itself recognized the address as invalid and returned a normal assistant message rather than a `function_call`.

This demonstrated two different layers:

1. The model may voluntarily avoid requesting a bad call.
2. Application validation independently blocks bad arguments if a call is requested.

Only the second should be treated as the enforceable security control.

---

## Policy Validation Beyond Schema Validation

A syntactically valid argument may still violate application policy.

A deterministic policy check was added:

```python
import ipaddress


def validate_ip_policy(ip: str):
    address = ipaddress.ip_address(ip)

    if not address.is_global:
        raise ValueError("non_public_ip_not_allowed")
```

`validate_ip_policy` was deliberately **not** added to `tools = []` because it is not a capability the model should call. It is an application-side policy gate.

Execution flow:

```text
LLM requests get_ip_reputation
        ↓
Pydantic validates IP syntax
        ↓
validate_ip_policy checks application policy
        ↓
real reputation function executes only if allowed
```

Test input:

```text
10.0.0.4
```

Pydantic accepted the address as syntactically valid, but the policy layer blocked it:

```text
BLOCKED: non_public_ip_not_allowed
```

This proved that **schema validity and authorization/policy validity are separate controls**.

---

## Insufficient-Evidence Test

The `bob` mock path was changed to return deliberately limited evidence:

```python
{
    "user": "bob",
    "failed_logins": 0,
    "successful_logins": 1,
    "last_source_ip": None
}
```

Request:

```text
Investigate user bob for suspicious activity.
```

Observed result:

```text
User bob shows no apparent suspicious authentication activity:

- Failed logins: 0
- Successful logins: 1
- Last source IP: Unavailable
```

The model did not invent an IP address, reputation result, or compromise claim. This satisfied the Lab 3 requirement that a tool-using investigation can recognize limited evidence rather than automatically escalate every request into a security incident.

---

# Questions and Answers

## What does it mean to expose a tool to the model?

It means supplying a model-facing tool definition containing the tool name, description, and argument schema. Defining a Python function alone does not expose it to the LLM.

## Does the model actually execute the Python function?

No. The model produces a structured function-call request. Application code inspects that request and decides whether to execute a function.

## What is `tools=tools`?

It is the list of tool definitions made available to that model request. It tells the model which functions it may request and the expected parameter structure.

## Can many tools be listed?

Yes, but exposing every tool to every request increases prompt/token overhead and increases the decision surface. Larger systems commonly select a relevant subset of tools for a given task.

## What is `call_id` for?

It associates a returned `function_call_output` with the exact function call that produced it.

## What is `previous_response_id` for?

It continues the previous Responses API interaction so the model can incorporate the tool results into the next step.

## Why use a registry instead of many `if` statements?

It provides scalable dispatch and, more importantly, makes the executable set explicit. The registry becomes a deterministic allowlist.

## If a tool appears in `tools=[]`, does that mean it is authorized to execute?

No. The model-facing definition controls what the model can request. The application-side registry/policy controls what is actually allowed to run.

## Should an unauthorized tool denial be sent back to the LLM?

Only when a model-generated explanation or permitted recovery path is useful. For terminal authorization failures, Python can end the workflow directly so the denial cannot be reinterpreted.

## Why did `300.300.300.40` return no `BLOCKED` line?

The model recognized that address as invalid and did not emit a function call. Since the validation code runs only on `function_call` items, the deterministic gate was never reached.

## Why did `30.300.30.40` produce `BLOCKED: invalid_arguments`?

The model attempted the tool call, but Pydantic independently validated the argument and rejected it as an invalid IP before the actual function could execute.

## Why is `validate_ip_policy` not in `tools=[]`?

Because it is not an LLM capability. It is an internal deterministic enforcement function that runs after an allowed tool request and argument validation.

## What is the difference between Pydantic validation and policy validation?

Pydantic answers: **is this argument structurally/type valid?**  
Policy answers: **even if valid, is this operation permitted?**

Example:

```text
10.0.0.4
```

is a valid IP address, so schema validation passes, but the lab policy rejects non-global addresses before calling the external-style reputation tool.

---

## Final Architecture Demonstrated

```text
Model request
    ↓
Model chooses one or more tools
    ↓
Python receives function_call
    ↓
Gate 1: execution allowlist
    ↓
Gate 2: Pydantic argument validation
    ↓
Gate 3: application policy validation
    ↓
Read-only function executes
    ↓
function_call_output + call_id
    ↓
Model correlates returned evidence
    ↓
Investigation summary
```

---

## Security Lessons

1. **Tool descriptions are not authorization controls.**
2. **The LLM requests; deterministic application code executes.**
3. **A tool allowlist is a separate boundary from the model-facing tool list.**
4. **Allowed tool does not imply trusted arguments.**
5. **Valid arguments do not imply policy-permitted arguments.**
6. **Hard security denials should remain deterministic.**
7. **Helpful model self-restraint is not an enforcement mechanism.**
8. **Tool evidence and model-generated conclusions must be distinguished.**
9. **Read-only tools are an appropriate first capability before state-changing tools.**

---

## What Was Demonstrated vs Guided

### Demonstrated hands-on

- Exposed custom function schemas to the model.
- Observed actual `function_call` output.
- Executed requested Python functions explicitly.
- Returned `function_call_output` using `call_id`.
- Continued model context with `previous_response_id`.
- Added a second read-only tool and observed model-selected multi-tool calls.
- Replaced hard-coded dispatch with a tool registry.
- Correlated multiple tool outputs in one model continuation.
- Tested an exposed-but-not-authorized `delete_user` request.
- Implemented deterministic tool execution allowlisting.
- Added Pydantic argument validation.
- Diagnosed model behavior when obviously invalid arguments caused no function call.
- Tested malformed-but-plausible IP input that reached and failed application validation.
- Added deterministic policy validation for non-global IPs.
- Demonstrated a valid-but-policy-disallowed argument.
- Tested an insufficient-evidence investigation path.

### Still guided / not yet demonstrated

- Reusable orchestration abstraction rather than a single explicit loop.
- Stateful workflow/state machine.
- State-changing tools with approval/authorization policy.
- Formal tool-permission objects or user/role-aware authorization.
- Repeatable evaluation harness.
- Bounded retry/self-correction.
- Real external investigation APIs.
- Persistent investigation state.
- Observability/tracing/token/cost instrumentation.

---

## Lab Result

**Lab 3 completed.**

The project now contains the core control boundary needed for agent tooling:

```text
LLM intent → deterministic authorization → validated arguments → policy check → execution
```

The next lab is **Lab 4 — Policy-Gated Tools**, where the system will begin separating model intent from authorization for actions that can potentially change state.