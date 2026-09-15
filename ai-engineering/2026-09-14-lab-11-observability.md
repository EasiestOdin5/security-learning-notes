# Lab 11 — AI Observability / Tracing / Cost

**Date:** September 14, 2026  
**Status:** Completed (first-pass scope)  
**File used:** `observability_lab.py`

---

## Goal

Make the agent observable enough to answer:

- what model call happened;
- how long it took;
- how many tokens it used;
- approximately what it cost;
- what tool the model requested;
- what the deterministic policy layer decided;
- whether tool execution succeeded or failed;
- what workflow state resulted;
- how to reconstruct one request from logs;
- how to summarize many requests into operational metrics and alerts.

The focus was not a production observability platform. The goal was to manually build the concepts that tools such as LangSmith, OpenTelemetry-based tracing, CloudWatch, OpenSearch, Datadog, or similar systems would automate or visualize.

---

## Architecture Built

```text
request
  ↓
request_id / trace correlation
  ↓
model_call event
  ├─ model
  ├─ latency
  ├─ input/output/total tokens
  ├─ estimated API cost
  └─ output
  ↓
tool_request event
  ↓
policy_decision event
  ├─ allow
  ├─ block
  └─ require_approval
  ↓
tool_execution event
  ├─ success
  └─ error
  ↓
state_transition event
  ↓
JSONL persistence
  ↓
per-request trace / summary
  ↓
aggregate metrics / rates / alerts
```

---

# 1. Model-call telemetry

Started with a normal Responses API call and measured elapsed time with `time.perf_counter()`.

```python
start_time = time.perf_counter()

response = client.responses.create(
    model="gpt-5.6-luna",
    input=prompt
)

end_time = time.perf_counter()
latency_seconds = end_time - start_time
```

Collected structured model telemetry:

```python
model_log = {
    "request_id": request_id,
    "event": "model_call",
    "model": response.model,
    "latency_seconds": round(latency_seconds, 3),
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens,
    "total_tokens": response.usage.total_tokens,
    "estimated_cost_usd": round(estimated_cost, 8),
    "output": response.output_text
}
```

Observed example:

```text
model: gpt-5.6-luna
latency: ~3 seconds
input tokens: 16
output tokens: ~48–50
total tokens: ~64–66
estimated cost: approximately $0.00006 per small test request
```

### Key lesson

A model call should not be treated only as:

```text
prompt → answer
```

It can also produce measurable telemetry:

```text
prompt → model → output + latency + tokens + cost
```

---

# 2. Request correlation

Added a UUID:

```python
request_id = str(uuid.uuid4())
```

Every event for one workflow uses the same `request_id`.

Conceptually:

```text
same request_id
├── model_call
├── tool_request
├── policy_decision
├── tool_execution
└── state_transition
```

This is the foundation of a trace.

---

# 3. Policy logging

A policy log records a deterministic security/control decision made by the application.

Example structure:

```python
policy_log = {
    "request_id": request_id,
    "event": "policy_decision",
    "tool": model_requested_tool,
    "decision": decision,
    "reason": reason
}
```

Dynamic policy logic:

```python
if model_requested_tool not in allowed_tools:
    decision = "block"
    reason = "unauthorized_tool"

elif model_requested_tool in high_risk_tools:
    decision = "require_approval"
    reason = "high_risk_tool"

else:
    decision = "allow"
    reason = "authorized_low_risk_tool"
```

### Important distinction

The model can request a tool without having authority to execute it.

```text
LLM requests tool
→ deterministic policy evaluates request
→ allow / require approval / block
```

The policy log is similar to an authorization/audit record: it says what rule outcome the application produced and why.

---

# 4. Tool request vs tool execution

Added a separate `tool_request` event:

```python
tool_request_log = {
    "request_id": request_id,
    "event": "tool_request",
    "tool": model_requested_tool
}
```

This captures **intent**.

Then a separate `tool_execution` event captures whether something actually happened.

Successful path:

```python
tool_execution_log = {
    "request_id": request_id,
    "event": "tool_execution",
    "tool": model_requested_tool,
    "status": "success",
    "result": tool_result
}
```

Failure path:

```python
error_log = {
    "request_id": request_id,
    "event": "tool_execution",
    "tool": model_requested_tool,
    "status": "error",
    "error": str(e)
}
```

### Key lesson

```text
tool_request = model wanted it
tool_execution = it actually ran
```

These are not equivalent.

---

# 5. Simulated tool failure

Used:

```python
raise RuntimeError("simulated_tool_failure")
```

This intentionally forced an execution error so the failure logging branch could be tested.

It does **not** mean the tool is dangerous. It is only test scaffolding.

The lab used:

```text
get_user_activity
→ simulated success

get_ip_reputation
→ allowed by policy
→ simulated execution failure
```

This exposed the distinction between:

```text
authorization success
```

and:

```text
execution success
```

A tool can be allowed and still fail operationally.

---

# 6. Workflow state and execution status

The standalone Lab 11 script is sequential code, not the full FSM from Labs 5/9.

A real state variable was introduced:

```python
current_state = "investigating"
execution_status = None
```

After policy and execution, the next state is calculated:

```python
if decision == "require_approval":
    next_state = "awaiting_approval"

elif decision == "block":
    next_state = "blocked"

elif execution_status == "success":
    next_state = "completed"

else:
    next_state = "blocked"
```

Then the simplified standalone script actually changes its state variable:

```python
old_state = current_state
current_state = next_state
```

Finally it logs the change:

```python
state_log = {
    "request_id": request_id,
    "event": "state_transition",
    "from_state": old_state,
    "to_state": current_state
}
```

### Resulting paths

```text
get_user_activity
→ allow
→ success
→ investigating → completed

get_ip_reputation
→ allow
→ execution error
→ investigating → blocked

disable_user
→ require_approval
→ no execution
→ investigating → awaiting_approval

unauthorized tool
→ block
→ investigating → blocked
```

### Important clarification

`execution_status = "error"` does not stop all state movement. It prevents the success path to `COMPLETED` and causes the workflow to move to `BLOCKED`.

---

# 7. Approval path limitation

The current Lab 11 script stops at:

```text
require_approval
→ awaiting_approval
```

It does not implement the later human approval action.

Conceptually, extra code would be required for:

```text
require_approval
→ human approves
→ decision becomes executable
→ tool runs
→ success/error handling
```

The fuller Lab 9 implementation already handled approval more correctly through a separate approval function and persisted pending actions. Lab 11 intentionally observes the flow instead of rebuilding the complete approval workflow.

---

# 8. Structured JSON logging

Created a reusable logger:

```python
def log_event(event):
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    json_line = json.dumps(event)
    print(json_line)

    with open("agent_trace.jsonl", "a") as log_file:
        log_file.write(json_line + "\n")
```

This produces one JSON object per line.

Example:

```json
{"request_id":"abc","event":"policy_decision","decision":"allow"}
```

### Python dict vs JSON

A Python dictionary is an in-memory object:

```python
{"event": "policy_decision"}
```

After:

```python
json.dumps(event)
```

it becomes a string containing JSON-formatted text.

```python
print(type(event))
# <class 'dict'>

print(type(json.dumps(event)))
# <class 'str'>
```

---

# 9. Persistent JSONL trace

The logger appends each event to:

```text
agent_trace.jsonl
```

Example conceptual file:

```text
{"request_id":"A","event":"model_call",...}
{"request_id":"A","event":"tool_request",...}
{"request_id":"A","event":"policy_decision",...}
{"request_id":"A","event":"tool_execution",...}
{"request_id":"A","event":"state_transition",...}
{"request_id":"B","event":"model_call",...}
...
```

This allows telemetry to survive process exit.

The implementation is intentionally local and simple; production would normally send events to a central backend.

---

# 10. Trace reconstruction

Implemented:

```python
show_trace(request_id)
```

It reads the JSONL file and displays only events matching the supplied request ID.

Because the script creates a new `request_id` on each run, calling:

```python
show_trace(request_id)
```

at the end of the run displays the current execution while ignoring older request IDs in the same file.

Example:

```text
TRACE:
... model_call
... tool_request
... policy_decision
... tool_execution
... state_transition
```

### Concept

```text
many log records
→ filter by request_id
→ reconstruct one request
```

---

# 11. Per-request summary

Implemented `summarize_trace(request_id)` to reduce multiple events into one high-level object.

Example observed summary:

```json
{
  "request_id": "...",
  "model": "gpt-5.6-luna",
  "latency_seconds": 2.951,
  "total_tokens": 65,
  "estimated_cost_usd": 0.000062,
  "tool": "get_ip_reputation",
  "policy_decision": "allow",
  "execution_status": "error",
  "final_state": "blocked"
}
```

This tells the full story in one place:

```text
tool requested
→ policy allowed it
→ execution failed
→ final state blocked
```

---

# 12. Debugging a real logging/schema bug

A `KeyError` occurred:

```text
KeyError: 'estimated_cost_usd'
```

The current `model_log` did contain the field, so the whole file was inspected.

Root cause: there were **two separate `model_call` events with the same request ID**:

- `model_log` — contained `estimated_cost_usd`;
- old `log_entry` — did not contain it.

`summarize_trace()` encountered the duplicate event and tried to read a field that was absent.

Fix: delete the stale duplicate `log_entry` block rather than hiding the current-schema bug with `.get()`.

### Lesson

Observability code has schemas too. Duplicate/inconsistent event schemas can make trace analysis misleading or fail outright.

---

# 13. Debugging trace consistency

Another issue was found when reviewing the full script:

The code initially logged:

```text
tool_request = get_user_activity
```

and later changed the variable to:

```text
get_ip_reputation
```

before policy/execution.

That meant the trace could claim the model requested one tool while the application actually evaluated another.

Fix: choose `model_requested_tool` before creating and logging the `tool_request` event.

### Lesson

Observability must reflect actual runtime behavior. A technically valid log that records the wrong event order or stale values can be more dangerous than no log because it creates false confidence.

---

# 14. High-risk tool policy bug

The code initially had:

```python
allowed_tools = {
    "get_user_activity",
    "get_ip_reputation"
}

high_risk_tools = {
    "disable_user"
}
```

Policy order was:

```python
if model_requested_tool not in allowed_tools:
    decision = "block"

elif model_requested_tool in high_risk_tools:
    decision = "require_approval"
```

Therefore `disable_user` could never reach `require_approval`; it was blocked first as unauthorized.

Correct model:

```python
allowed_tools = {
    "get_user_activity",
    "get_ip_reputation",
    "disable_user"
}

high_risk_tools = {
    "disable_user"
}
```

Interpretation:

```text
allowed_tools
= tools this context may use at all

high_risk_tools
= subset of allowed tools requiring extra approval
```

---

# 15. Why `execution_status` can be null

For a high-risk tool awaiting approval:

```text
policy_decision = require_approval
```

The execution block is never entered.

Therefore:

```python
execution_status = None
```

becomes:

```json
"execution_status": null
```

This means:

```text
tool not executed
```

not:

```text
tool failed
```

An actual execution failure is represented as:

```json
"execution_status": "error"
```

---

# 16. Cost telemetry

Added approximate API cost from token counts.

```python
input_cost = (
    response.usage.input_tokens / 1_000_000
) * INPUT_COST_PER_MILLION

output_cost = (
    response.usage.output_tokens / 1_000_000
) * OUTPUT_COST_PER_MILLION

estimated_cost = input_cost + output_cost
```

Example observed:

```text
16 input tokens
48 output tokens
estimated_cost_usd = 6.08e-05
```

Scientific notation:

```text
6.08e-05 = $0.0000608
```

### Important distinction

Cost telemetry is about the model/API call, not the workflow state machine.

```text
model telemetry
→ latency / tokens / cost

workflow telemetry
→ tool / policy / execution / state
```

The `request_id` correlates them into one trace.

---

# 17. Aggregate metrics

Implemented `summarize_all_traces()` to group events by `request_id` and calculate application-wide metrics.

Metrics included:

```text
total requests
average model latency
total tokens
estimated total cost
execution error count
completed count
blocked count
awaiting approval count
```

Observed example during test-heavy traffic:

```json
{
  "total_requests": 12,
  "average_latency_seconds": 3.24,
  "total_tokens": 794,
  "estimated_total_cost_usd": 0.0005724,
  "execution_errors": 6,
  "completed": 3,
  "blocked": 9,
  "awaiting_approval": 0
}
```

### Important lesson

The log file contained many deliberately failing experiments, so aggregate metrics were heavily biased toward blocked/error traffic.

```text
observed metrics
≠ automatically normal production behavior
```

You must understand the traffic population that produced a metric.

Test traffic can distort production-style dashboards.

---

# 18. Rates

Converted counts into rates:

```python
execution_error_rate = execution_errors / total_requests
blocked_rate = blocked / total_requests
approval_rate = awaiting_approval / total_requests
```

Observed example:

```json
{
  "execution_error_rate": 0.5,
  "blocked_rate": 0.75,
  "approval_rate": 0.0
}
```

Interpretation:

```text
execution_error_rate = 50%
blocked_rate = 75%
approval_rate = 0%
```

### Lesson

Counts answer:

```text
How many failures happened?
```

Rates answer:

```text
What fraction of requests failed?
```

Rates are easier to compare when traffic volume changes.

---

# 19. Threshold alerts

Added simple health checks:

```python
if metrics["execution_error_rate"] > 0.25:
    print("ALERT: high tool execution error rate")

if metrics["blocked_rate"] > 0.50:
    print("ALERT: high blocked-request rate")
```

Observed:

```text
ALERT: high tool execution error rate
ALERT: high blocked-request rate
```

The thresholds are lab values only.

Production thresholds should be based on expected behavior, historical baseline, service objectives, and traffic composition.

The final observability pipeline became:

```text
raw events
→ persistent JSONL
→ per-request trace
→ per-request summary
→ aggregate metrics
→ rates
→ threshold-based alerts
```

---

# Questions and Answers

## Q: What is a policy log conceptually?

A policy log records a deterministic security/control decision made by the application: what was requested, what rule was evaluated, what decision was produced, and why.

It is comparable to an authorization/audit log.

---

## Q: The policy log values were originally static. What was the point?

The first version only established the event schema. It became meaningful once the fields were populated from real runtime policy logic.

Static demo fields should not be confused with actual telemetry.

---

## Q: How can I tell a Python dict from JSON?

A dict is a Python object. `json.dumps()` serializes it into a string containing JSON-formatted text.

`type(dict)` is `dict`; `type(json.dumps(dict))` is `str`.

---

## Q: Is `simulated_tool_failure` saying every tool except `get_user_activity` is dangerous?

No. It is an intentionally raised exception used to test the failure logging path.

Danger/risk is determined by policy (`allowed_tools`, `high_risk_tools`), not by the fake execution stub.

---

## Q: If policy says a tool is allowed, what happens next?

Authorization and execution are separate.

```text
policy says allow
→ attempt execution
→ success or failure
```

An allowed tool can still fail.

---

## Q: Why is this related to AI? Isn't `try/except` just general software engineering?

Correct: exception handling, JSON logging, files, and thresholds are general software engineering.

The AI-specific observability is **what is being traced together**:

- model choice;
- prompt/model latency;
- token usage and cost;
- model-requested tools;
- deterministic policy decisions;
- tool execution;
- agent state transitions;
- retries/approvals/errors.

The lab only counts as AI observability because the general mechanisms are tied to nondeterministic model behavior and agent workflow control.

---

## Q: Would production use LangSmith?

LangSmith is one reasonable production choice for LLM/agent tracing. Similar functions can be provided by OpenTelemetry-based instrumentation, Datadog, OpenSearch, CloudWatch, or other observability systems.

The manual lab is useful because it exposes what such platforms are recording rather than treating tracing as magic.

The deterministic security/policy logic still belongs in the application; an observability platform only records and analyzes it.

---

## Q: In this script there is no FSM function call. How does state actually change?

The standalone script executes top-to-bottom and uses a normal variable:

```python
current_state = "investigating"
...
current_state = next_state
```

`next_state` calculates the desired destination; assigning it to `current_state` performs the simplified state change; logging records what happened.

This is intentionally simpler than the real FSM from Labs 5/9.

---

## Q: If tool execution fails, does that prevent all state transitions?

No. It prevents the success transition to `COMPLETED`.

The failure still produces a transition:

```text
investigating
→ execution error
→ blocked
```

---

## Q: If a high-risk tool is approved, would extra code be required to execute it?

Yes. The current Lab 11 script only reaches `awaiting_approval`.

A later approval event would need to authorize execution and then reuse success/failure handling. Lab 9 already implemented a fuller approval workflow.

---

## Q: `show_trace(request_id)` uses which request?

It uses the UUID created for the current script execution. Older events remain in the JSONL file but are filtered out because they have different request IDs.

---

## Q: Why did `summarize_trace()` throw `KeyError: estimated_cost_usd` even though `model_log` contained the key?

There was a second stale `model_call` event (`log_entry`) with the same request ID that did not contain that field. The correct fix was to remove the duplicate current-schema event rather than merely mask the problem.

---

## Q: Why did `disable_user` show `block` instead of `require_approval`?

Because it was listed as high risk but was not in `allowed_tools`. The first policy branch rejected it before the high-risk branch could run.

A high-risk tool must be an allowed capability first, then marked as requiring extra approval.

---

## Q: Why was `execution_status` null for `disable_user`?

Because the policy stopped at `require_approval`. The tool never executed, so execution status correctly remained `None`/JSON `null`.

---

# Troubleshooting / Process Lessons

## Incomplete code-fragment problem

During the lab, several code changes were initially supplied as snippets without making all structural changes explicit. This caused confusion around:

- initialization of `execution_status`;
- introduction of `current_state`;
- difference between calculating `next_state`, changing state, and logging state;
- where blocks belonged in the sequential script.

The user correctly identified that a learner should not be expected to infer omitted variables or reconstruct a larger refactor from partial snippets.

A useful standard for future labs:

- clearly label changes as **ADD**, **REPLACE**, or **REMOVE**;
- when control flow changes materially, provide the full affected block;
- distinguish simulated state/logging from a real FSM transition.

## Capability assessment from the questions

The user demonstrated correct reasoning about:

- authorization vs execution success;
- simulated failure vs tool risk;
- model intent vs deterministic policy decision;
- logging a state transition vs actually changing state;
- `None`/`null` meaning no execution rather than failure;
- general software engineering mechanisms vs AI-specific observability context;
- interpreting traces as black-box evidence of workflow behavior.

The main remaining gap is implementation fluency when several Python variables/branches are introduced simultaneously, not the core architecture concepts.

---

# Security / Reliability Implications

1. **Trace intent separately from execution.** A model request is not proof an action occurred.
2. **Log deterministic policy decisions.** This provides an auditable explanation of why an action was allowed, blocked, or held for approval.
3. **Record failures explicitly.** Authorization success must not be mistaken for execution success.
4. **Correlate with request IDs.** Without correlation, model/tool/state events are difficult to reconstruct reliably.
5. **Keep event schemas consistent.** Duplicate or stale schemas can break summaries and produce misleading telemetry.
6. **Watch for stale runtime values.** Logging a tool name before later changing the variable creates a false trace.
7. **Metrics need context.** Test-heavy traffic can produce alarming rates that do not represent normal production behavior.
8. **Thresholds are not universal.** Alert values require baseline tuning.
9. **Observability is not authorization.** Logging tools show what happened; they do not replace deterministic policy controls.

---

# What Was Demonstrated

- structured model-call telemetry;
- latency measurement;
- token usage capture;
- approximate per-call cost;
- UUID trace correlation;
- tool request logging;
- dynamic policy decision logging;
- success/error tool execution logging;
- simplified state-transition logging;
- JSON serialization;
- persistent JSONL logging;
- per-request trace reconstruction;
- per-request summary generation;
- aggregate metrics across requests;
- error/block/approval rates;
- threshold-based alerts;
- debugging of inconsistent observability schemas and stale trace values.

---

# Limitations / Not Yet Implemented

- no OpenTelemetry instrumentation;
- no LangSmith/Datadog/OpenSearch/CloudWatch backend;
- no spans or parent/child trace hierarchy;
- no real distributed tracing across multiple services;
- no production log rotation or retention;
- no asynchronous/batched exporter;
- no durable centralized log store;
- no dashboards;
- no percentile latency (`p50`, `p95`, `p99`);
- no per-tool latency metrics;
- no retry counters in the trace;
- no model/provider error classification;
- no production cost-pricing abstraction;
- no automated schema/version management;
- no redaction/DLP applied to observability payloads;
- no correlation with the persisted Lab 9 database;
- no direct instrumentation of the real FSM transition method;
- no real human approval continuation in this standalone script;
- no service-level objectives or baseline-derived alert thresholds.

---

# Strict Score Change

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| AI Observability / Tracing / Cost | 1.5 | 3.0 | Implemented structured correlated model/tool/policy/state telemetry, JSONL persistence, latency/token/cost tracking, per-request traces and summaries, aggregate metrics/rates, and threshold alerts |

No other score increases are justified by this lab. The underlying tool calling, policy, and state concepts were mostly reused from prior labs.

The score remains conservative because the work was guided and local-only, with no production tracing backend, distributed spans, dashboards, percentile metrics, schema management, or real multi-service deployment.

---

# Next Lab

**Lab 12 — Cloud / Kubernetes Deployment**

Expected focus:

- containerizing the more complete AI application;
- workload identity;
- secrets handling;
- least privilege;
- network controls;
- Kubernetes/ECS-style deployment boundaries;
- operational logging/observability integration.
