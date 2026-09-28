# Pass 2 — Lab 3: Read-Only Investigation Tools

**Date completed:** September 28, 2026  
**Status:** Completed  
**Pass:** Pass 2 — guided design, increasingly independent implementation

---

## Goal

Rebuild the read-only tool-calling workflow from the first pass without copying the original implementation.

Target architecture:

```text
Security alert
    ↓
LLM receives available tool interfaces
    ↓
LLM requests one or more tools
    ↓
Python parses function_call items
    ↓
Deterministic allowlist check
    ↓
Pydantic argument validation
    ↓
Python executes real functions
    ↓
Tool outputs returned with call_id
    ↓
LLM produces final structured assessment
```

The central design principle is that the model may **request** a tool, but deterministic application code controls validation and execution.

---

## Files / Application Structure

The investigation functions were moved out of `main.py` into:

```text
ai-agent-lab-pass2/
├── main.py
├── investigation_tools.py
└── Dockerfile
```

The Dockerfile was updated to copy both Python files.

This separation reinforced the distinction between:

- the **interface exposed to the LLM**;
- the **Python execution implementation**;
- the **dispatch/allowlist table** that connects them.

---

## Read-Only Tool Implementations

Two simulated investigation functions were implemented.

### `get_ip_reputation(ip: str)`

Behavior:

- `8.8.8.8` → suspicious, score 82
- `1.1.1.1` → benign, score 5
- anything else → unknown, score 0

Example result:

```python
{
    "ip": "8.8.8.8",
    "reputation": "suspicious",
    "score": 82
}
```

### `get_user_activity(username: str)`

The implementation used a default dictionary and then selectively overrode values for known users.

Behavior:

- `alice` → 7 failed, 1 successful, last IP 8.8.8.8
- `bob` → 0 failed, 1 successful, last IP None
- other → 0 failed, 0 successful, last IP None

This avoided repeating the entire return dictionary in every branch.

---

## OpenAI Tool Definitions

A `tools` list was created for the Responses API.

Each entry included:

- `type: "function"`
- function `name`
- human-readable `description`
- `strict: True`
- JSON Schema under `parameters`

Example conceptual shape:

```python
{
    "type": "function",
    "name": "get_ip_reputation",
    "description": "Look up the reputation of an IP address",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "ip": {
                "type": "string",
                "description": "IP address to investigate"
            }
        },
        "required": ["ip"],
        "additionalProperties": False
    }
}
```

The same pattern was used for `get_user_activity`.

---

## JSON Schema Concepts Learned

JSON Schema was new in this pass.

The important distinction established was:

- **OpenAI defines the outer tool format** such as `type`, `name`, `description`, `parameters`, and `strict`.
- **JSON Schema defines the argument contract inside `parameters`**.

For this lab, the important JSON Schema keywords were:

- `type`
- `properties`
- `description`
- `required`
- `additionalProperties`
- `enum`

`strict: True` improves conformance to the declared argument schema, but it does not establish semantic validity. For example, `{"ip": "hello"}` is still a string and therefore requires application-side validation.

---

## First Tool-Selection Test

A new `/investigate` endpoint called:

```python
client.responses.create(
    model="gpt-5.6-luna",
    input=request.message,
    tools=tools
)
```

The Alice alert used for testing described:

- 12 failed login attempts;
- one successful login;
- source IP `8.8.8.8`;
- successful login at 03:15 AM;
- unfamiliar device.

The model returned two `function_call` items:

```text
get_user_activity({"username":"alice"})
get_ip_reputation({"ip":"8.8.8.8"})
```

The calls were independent in this case because neither required the other's output before execution.

---

## Understanding `response.output`

A major API concept clarified during the lab was the difference between:

- `response.output` — a list of structured SDK output objects;
- `response.output_text` — convenience text extracted from text-message output;
- `response.output_parsed` — Pydantic-parsed structured output when using `responses.parse()`.

Example hierarchy observed:

```text
response
  └── output
       └── [0] ResponseOutputMessage
            └── content
                 └── [0] ResponseOutputText
                      └── text
```

For tool calling, `response.output` is required because function calls appear as structured response items rather than ordinary text.

---

## Parsing Tool Requests

The endpoint iterated over `response.output` and selected:

```python
if output.type == "function_call":
```

For each request, it extracted:

- `output.name`
- `output.arguments`
- `output.call_id`

The original implementation accidentally used `output.id`; this was corrected to `output.call_id`.

`call_id` is the identifier used later to associate a function result with the function call that requested it.

---

## JSON Argument Conversion

`output.arguments` is JSON text, not already a Python dictionary.

The conversion path became:

```text
LLM arguments JSON string
    ↓
json.loads(...)
    ↓
Python dict
```

This also clarified the inverse:

```text
Python object
    ↓
json.dumps(...)
    ↓
JSON-formatted string
```

The difference between `json.load()` and `json.loads()` was also reviewed:

- `load()` reads JSON from a file-like object.
- `loads()` parses JSON from a string.

---

## Python Dispatch / Allowlist Mapping

A Python-side dispatch table was built:

```python
tool_functions = {
    "get_ip_reputation": (get_ip_reputation, IPReputationArgs),
    "get_user_activity": (get_user_activity, UserActivityArgs)
}
```

This serves two roles:

1. map the model's requested tool name to the real Python function;
2. independently limit execution to known/allowed functions.

The LLM-facing `tools` list and Python-side `tool_functions` registry therefore have different purposes.

---

## Argument Validation

Pydantic argument models were created:

```python
class IPReputationArgs(BaseModel):
    ip: IPvAnyAddress

class UserActivityArgs(BaseModel):
    username: str = Field(..., min_length=1)
```

The execution path used:

```python
validated_args = args_model.model_validate(result["arguments"])
validated_args = validated_args.model_dump(mode="json")
tool_result = tool_function(**validated_args)
```

Conceptually:

```text
JSON string
→ json.loads()
→ Python dict
→ Pydantic model_validate()
→ validated Pydantic object
→ model_dump(mode="json")
→ plain dict
→ **dict
→ real Python function call
```

The `**validated_args` operation was reviewed explicitly:

```python
{"ip": "8.8.8.8"}
```

becomes equivalent to:

```python
get_ip_reputation(ip="8.8.8.8")
```

---

## Verified Local Tool Execution

The Alice alert produced:

```text
ALLOWED: get_user_activity
Validated arguments: username='alice'
Tool result:
{'username': 'alice', 'failed_logins': 7, 'successful_logins': 1, 'last_ip': '8.8.8.8'}

ALLOWED: get_ip_reputation
Validated arguments: ip=IPv4Address('8.8.8.8')
Tool result:
{'ip': '8.8.8.8', 'reputation': 'suspicious', 'score': 82}
```

This verified:

```text
LLM tool request
→ deterministic allowlist
→ argument validation
→ real function execution
```

---

## Returning Tool Results to the Model

The Python function result was converted into a Responses API `function_call_output` item:

```python
{
    "type": "function_call_output",
    "call_id": result["call_id"],
    "output": json.dumps(tool_result)
}
```

Important distinction:

- the outer item is a structured Python object/list;
- the `output` field itself is a JSON-formatted string.

A second model call was then linked to the first with:

```python
previous_response_id=response.id
```

This preserves the prior context so the model knows which earlier tool calls the returned `call_id` values answer.

---

## Free-Form Final Result and Grounding Issue

The first completed two-call workflow returned readable investigation prose.

The model correctly incorporated:

- suspicious IP reputation score 82;
- user activity showing 7 failed and 1 successful login;
- the original alert's 12 failed attempts;
- the discrepancy between 12 and 7.

However, it also claimed:

> "I'm checking the authentication event details and device context..."

No tool existed for those checks.

This was identified as a **grounding hallucination / unsupported claim**: the model implied evidence retrieval that had not occurred.

A second content-quality concern was that the model's conclusion could sound stronger than the limited and inconsistent evidence supported.

These issues were deliberately separated from the output-format problem.

---

## Structured Final Assessment

A structured final model was created by reusing the existing `Classification` and `Severity` enums:

```python
class InvestigationAssessment(BaseModel):
    classification: Classification
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_used: list[str]
    unresolved_questions: list[str]
    recommended_actions: list[str]
    reason: str = Field(..., min_length=1)
```

The second model call was changed from `responses.create()` to `responses.parse()` with:

```python
text_format=InvestigationAssessment
```

The final tested output was:

- classification: suspicious
- severity: high
- confidence: 0.91
- explicit evidence list
- explicit unresolved questions
- recommended actions
- bounded reasoning text

The model explicitly preserved the 12-vs-7 discrepancy rather than silently reconciling it.

---

## Questions and Answers

### What does it mean that the LLM should not execute Python directly?

The model proposes a structured tool request. Python determines whether that tool is allowed, validates its arguments, and performs the real execution.

### How is deterministic execution different from simply executing what the model requests?

Without a deterministic gate, every requested known function could execute automatically. The application-side layer provides an independent authority boundary for allowlisting, validation, policy, and later human approval.

### Are the two Alice tool calls order-dependent?

No. `get_user_activity("alice")` and `get_ip_reputation("8.8.8.8")` are independent. Dependent calls would require returning one result to the model before it could determine the next tool request.

### Can an investigation require many rounds of tools?

Yes. A real agent may need:

```text
model → tool → result → model → another tool → result → model
```

A production implementation would bound the number of iterations and tool calls. This lab implemented one tool-selection round followed by final assessment.

### Is the tool list like a vtable or COM interface?

As a mental model, yes at a high level. The `tools` list declares callable interfaces and argument contracts, while the Python implementation remains behind that interface. Unlike COM, this is JSON-based and probabilistic rather than a rigid binary interface.

### What is a software "contract"?

A contract is the agreement between components about expected inputs, outputs, and behavior.

In this lab:

- JSON Schema expresses part of the model-facing input contract.
- Pydantic enforces part of the Python-side input contract.
- function return dictionaries currently form an informal output contract.
- behavioral expectations define what each tool is supposed to do.

### Can the tool implementation change without changing the rest of the system?

Yes, provided the contract remains compatible. A hardcoded IP lookup could later be replaced with a real reputation API without changing the calling interface, if its inputs and outputs remain compatible.

### Is `tools` itself the executable function list?

No. `tools` tells the LLM what operations it may request. `tool_functions` maps those requested names to actual executable Python functions.

### Why is `response.output` different from `response.output_text`?

`response.output` exposes all structured response items, including function calls. `output_text` only extracts normal text output.

### Is `response.output_parsed` only relevant with `responses.parse()`?

Yes. It is the convenience object produced when the final output is parsed into the supplied Pydantic model.

### Why use `json.loads()`?

The model returns function arguments as JSON text. `json.loads()` converts that text into a Python dictionary.

### Why use `json.dumps(tool_result)`?

The Responses API `function_call_output.output` field expects a string. `json.dumps()` serializes the Python dictionary into a JSON-formatted string.

### What does `previous_response_id` do?

It links the second response call to the context of the first one so the model understands the original alert, the earlier function calls, and the returned `call_id` values.

### Why use structured output for the final investigation?

Free-form prose makes downstream processing and grounding boundaries harder to control. A Pydantic schema forces the model to populate defined fields such as evidence, unresolved questions, and recommended actions.

---

## What Was Independent vs Guided

### Independent / increasingly independent

- implemented both simulated Python tools;
- chose a default-dictionary pattern for user activity rather than copying the IP function structure;
- separated functions into `investigation_tools.py`;
- wrote both tool-definition dictionaries;
- wrote the `/investigate` endpoint;
- iterated over `response.output`;
- built a list of extracted tool requests;
- constructed the Python dispatch mapping;
- created Pydantic argument models;
- connected validated arguments to the real functions;
- created the function-call output objects;
- completed the second Responses API call;
- implemented the final structured `InvestigationAssessment` model;
- tested the full alert → tools → result → assessment flow.

### Guided / corrected

- JSON Schema syntax and purpose;
- OpenAI tool-definition format and `strict=True`;
- `response.output` versus `output_text` / `output_parsed`;
- `output.call_id` versus `output.id`;
- `json.loads()` versus `json.load()`;
- tuple unpacking from `tool_functions`;
- use of `model_validate()`, `model_dump(mode="json")`, and `**kwargs`;
- exact `function_call_output` shape;
- use of `previous_response_id`;
- shift from free-form final output to `responses.parse()`;
- grounding/hallucination analysis.

The architecture and progression remained guided. This is stronger evidence than Pass 1 for implementation understanding, but not yet evidence of independently designing a robust multi-step agent system.

---

## Remaining Limitations

The core Lab 3 path is complete, but several production-level issues remain:

- invalid Pydantic tool arguments are not yet handled with a controlled error path;
- the current flow handles one tool-selection round rather than an arbitrary bounded loop;
- model confidence is not calibrated;
- `evidence_used` still mixes original alert claims and tool-verified evidence;
- the model can still make unsupported claims unless grounding constraints are strengthened;
- output contracts for the Python tools are informal dictionaries rather than explicit models;
- no concurrency/parallel execution was implemented for independent calls;
- no automated regression tests were added for tool selection or grounding behavior.

---

## Conservative Score Changes

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| LLM API Fundamentals | 3.25 | 3.5 | Rebuilt function-call continuation with structured response items, call IDs, previous-response context, and parsed final output |
| Structured Outputs / Schemas | 4.0 | 4.25 | Added JSON Schema tool contracts, Pydantic argument validation, and a structured final investigation model |
| Tool / Function Calling | 3.75 | 4.25 | Independently implemented most of the request → dispatch → validate → execute → return-output path |
| Agent Orchestration | 3.0 | 3.25 | Completed a two-stage model/tool/model workflow with multiple independent tool calls |
| Deterministic Gates / Policy Controls | 5.5 | 5.75 | Rebuilt a Python execution allowlist plus per-tool Pydantic argument validation |

No Agent Security score increase: recognizing the grounding hallucination was useful, but no new grounding/security control was independently implemented in this lab.

---

## Main Takeaway

The full read-only tool interface is now working:

```text
LLM sees declared interfaces
→ requests specific tools
→ Python independently validates and dispatches
→ implementations return evidence
→ evidence is correlated through call_id
→ model produces a structured assessment
```

The most important conceptual advance was recognizing that **tool interfaces, implementation, contracts, dispatch, validation, and final model output are separate layers**. The remaining challenge is making the overall agent loop more independent, bounded, and grounded.
