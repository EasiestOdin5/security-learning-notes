# AI Engineering Lab 7 — Bounded Self-Correction

**Date:** September 4, 2026  
**Status:** Completed  
**Primary skill:** Self-Correction / Bounded Retry

---

## Goal

Build a small, understandable retry controller where:

1. an attempt runs,
2. a deterministic evaluator checks the result,
3. failure produces explicit feedback,
4. the feedback is supplied to the next attempt,
5. Python enforces a hard maximum number of attempts,
6. the workflow either passes or stops.

The goal was not to build a large autonomous agent loop. The lab intentionally isolated bounded correction from tool orchestration so the retry boundary remained easy to inspect.

---

## Core Architecture

```text
attempt 1
   ↓
model/function output
   ↓
deterministic evaluator
   ↓
PASS ───────────────→ return result
   ↓ FAIL
specific feedback
   ↓
retry allowed only if attempts remain
   ↓
attempt 2
   ↓
evaluate again
   ↓
PASS → return
FAIL → hard stop
```

The important boundary is that the LLM does not decide whether it may retry indefinitely. Deterministic Python owns `MAX_ATTEMPTS`.

---

## Step 1 — Basic Bounded Retry Controller

Created `retry_lab.py` with:

```python
MAX_ATTEMPTS = 2


def run_with_retry(run_once, prompt, evaluator):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = run_once(prompt)

        if evaluator(result):
            print(f"PASS on attempt {attempt}")
            return result

        print(f"FAILED evaluation on attempt {attempt}")

    print("STOPPED: maximum attempts reached")
    return None
```

### Initial toy test

A fake runner intentionally returned a bad result on the first call and a good result on the second:

```python
attempt_counter = 0


def fake_run(prompt):
    global attempt_counter
    attempt_counter += 1

    if attempt_counter == 1:
        return {"status": "bad"}

    return {"status": "good"}
```

The first test produced:

```text
FAILED evaluation on attempt 1
PASS on attempt 2
```

### Lesson

This proved retry control, but not self-correction. The second result became good because of a counter, not because the previous failure taught the next attempt anything.

---

## Step 2 — Add Evaluator Feedback

Changed the evaluator contract from a Boolean to `(passed, feedback)`:

```python
def fake_evaluator(result):
    if result["status"] == "good":
        return True, None

    return False, "status must be good"
```

Then changed the retry controller so the next attempt receives that feedback:

```python
def run_with_retry(run_once, prompt, evaluator):
    feedback = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = run_once(prompt, feedback)

        passed, feedback = evaluator(result)

        if passed:
            print(f"PASS on attempt {attempt}")
            return result

        print(f"FAILED evaluation on attempt {attempt}: {feedback}")

    print("STOPPED: maximum attempts reached")
    return None
```

The fake runner was then changed to react only to the specific expected feedback:

```python
def fake_run(prompt, feedback):
    if feedback == "status must be good":
        return {"status": "good"}

    return {"status": "bad"}
```

### Why this mattered

The second attempt now changed behavior because it received a specific correction signal rather than merely because it was attempt number two.

---

## Step 3 — Prove the Hard Failure Boundary

The evaluator was temporarily changed to return feedback the fake runner did not recognize.

Observed behavior:

```text
FAILED evaluation on attempt 1: wrong feedback
FAILED evaluation on attempt 2: wrong feedback
STOPPED: maximum attempts reached
```

This proved that feedback does not guarantee success and that the controller stops at the deterministic limit.

---

## Step 4 — Attempt Integration with the Existing Investigation Agent

A wrapper was added around the existing `run_request()` flow:

```python
from test_tool import run_request


def real_run(prompt, feedback):
    if feedback is None:
        return run_request(prompt)

    corrected_prompt = (
        f"{prompt}\n"
        f"Previous attempt failed evaluation because: {feedback}\n"
        "Correct the previous attempt."
    )

    return run_request(corrected_prompt)
```

A real evaluator checked expected workflow state and expected tool usage.

### First ground-truth mistake

Prompt:

```text
Investigate whether user alice should be disabled.
```

The model chose `get_user_activity`, and the workflow ended:

```text
NEW → INVESTIGATING → COMPLETED
```

The evaluator originally expected:

```text
state = awaiting_approval
tool = disable_user
```

That expectation was too aggressive. The prompt asked the system to investigate whether Alice should be disabled; gathering user activity and completing the current single-pass investigation was a reasonable result under the existing code.

The ground truth was corrected to:

```text
state = completed
tool = get_user_activity
```

The test then passed on attempt 1.

### Lesson

Evaluator ground truth must represent what the prompt actually requires. A retry system should not force a model toward an unjustified action merely because the test author expected it.

---

## Step 5 — Explicit Action Case

A stronger prompt supplied both evidence and policy:

```text
User alice has 7 failed logins and 1 successful login from 8.8.8.8.
Policy requires disabling the account for this condition.
Take the required action.
```

Expected:

```text
state = awaiting_approval
tool = disable_user
```

Observed:

```text
NEW → INVESTIGATING → AWAITING_APPROVAL
PENDING APPROVAL ... disable_user {'user': 'alice'}
PASS on attempt 1
```

This established that the ground truth was valid when the requirement was explicit.

---

## Step 6 — Discover an Orchestration Limitation

A less explicit prompt was then used:

```text
User alice has suspicious authentication activity.
Company policy requires accounts with confirmed suspicious activity to be disabled.
Investigate and handle the incident.
```

Attempt 1:

```text
NEW → INVESTIGATING
get_user_activity
NEW evidence returned
INVESTIGATING → COMPLETED
```

The evaluator returned specific feedback:

```text
Expected state 'awaiting_approval' and tool 'disable_user'.
Got state 'completed' and tools ['get_user_activity'].
```

Attempt 2 still repeated `get_user_activity` and completed.

### Root cause

This was not a failure of the retry counter. The existing `test_tool.py` architecture processes the first tool call and obtains a later model response, but it does not continue processing another tool call from that later response as a new orchestration cycle.

Therefore a pattern such as:

```text
investigate
→ get_user_activity
→ reason over evidence
→ request disable_user
```

is not fully supported by the current single-pass tool workflow.

### Scope decision

The lab did **not** expand `run_request()` into a general multi-tool while-loop. A similar experiment in Lab 4 created repeated-call complexity and lab bloat. Multi-step orchestration is intentionally deferred to a later advanced pass.

---

## Step 7 — Isolate Real LLM Self-Correction

To prove actual model correction cleanly, tool orchestration was removed from this portion of the lab.

Created a plain LLM runner:

```python
from openai import OpenAI

client = OpenAI()


def answer_once(prompt, feedback):
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    if feedback is not None:
        messages.append(
            {
                "role": "user",
                "content": f"Previous answer failed because: {feedback}"
            }
        )

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=messages
    )

    return response.output_text
```

The deterministic evaluator required exactly one output:

```python
def answer_evaluator(result):
    if result.strip() == "SAFE":
        return True, None

    return False, f"Expected exactly 'SAFE', got: {result!r}"
```

---

## Step 8 — Real LLM Correction Test

Prompt:

```text
Explain briefly why a verified benign security artifact is safe.
```

The prompt naturally encourages explanation, while the evaluator requires exactly `SAFE`.

### Attempt 1

Model returned a normal explanatory paragraph.

Evaluator:

```text
passed: False
feedback: Expected exactly 'SAFE', got: '<long answer>'
```

### Attempt 2

The model received both:

```text
user: Explain briefly why a verified benign security artifact is safe.
user: Previous answer failed because: Expected exactly 'SAFE', got: '<long answer>'
```

The model then returned:

```text
SAFE
```

Evaluator:

```text
passed: True
feedback: None
```

Final result:

```text
PASS on attempt 2
```

This was the first real demonstration in the lab where an actual LLM changed its output because of deterministic evaluator feedback.

---

## Step 9 — Make the Correction Path Observable

The retry code was updated to print each attempt's exact model input, model output, evaluator result, and feedback.

Example trace:

```text
========== ATTEMPT 1 ==========

MODEL INPUT:
user: Explain briefly why a verified benign security artifact is safe.

MODEL OUTPUT:
<long explanatory answer>

EVALUATOR RESULT:
passed: False
feedback: Expected exactly 'SAFE', got: '<long explanatory answer>'

FAILED evaluation on attempt 1

========== ATTEMPT 2 ==========

MODEL INPUT:
user: Explain briefly why a verified benign security artifact is safe.
user: Previous answer failed because: Expected exactly 'SAFE', got: '<long explanatory answer>'

MODEL OUTPUT:
SAFE

EVALUATOR RESULT:
passed: True
feedback: None

PASS on attempt 2
```

### Lesson

The retry controller does not fix the answer itself. It transports a deterministic evaluator's feedback into the next model input and permits another attempt only while the retry budget remains.

---

## Step 10 — Real LLM Hard-Stop Test

The evaluator was temporarily made impossible to satisfy:

```python
def answer_evaluator(result):
    return False, "This test intentionally never passes."
```

Observed:

```text
attempt 1 → FAIL
attempt 2 → FAIL
STOPPED: maximum attempts reached
```

The normal evaluator was then restored.

This proved the hard retry boundary with the real LLM, not only with the fake function.

---

# Questions and Answers

## Q: In the first fake example, did the second call simply return good because it was the second attempt?

Yes. That first version only proved retry mechanics. It did not prove self-correction.

## Q: Was there any specific fix being applied in the first version?

No. It merely reran. Actual correction began when evaluator feedback was passed into the next attempt.

## Q: If `fake_run()` treats any feedback as success, is that meaningful?

Not very. It proves feedback transport, but not specific correction. The fake runner was tightened so only the expected feedback changed its result.

## Q: Are we expecting the LLM to use the feedback?

Yes. In the real correction path, the second attempt receives the original prompt plus a new message describing why the previous output failed.

## Q: Why did the first Alice test end `NEW → INVESTIGATING → COMPLETED`?

Because the prompt asked whether Alice should be disabled. The model reasonably chose a read-only investigation tool, and the current single-pass workflow completed after that investigation. The evaluator's original expectation of `disable_user` was not justified by the prompt.

## Q: Why did the more realistic Alice correction case fail twice even after feedback explicitly said to use `disable_user`?

Because the current agent architecture does not fully support a second tool-calling cycle after processing the first investigation tool result. This is an orchestration limitation, not evidence that bounded retry itself is broken.

## Q: Why not fix that by adding a while-loop now?

Because multi-turn tool orchestration adds another major concept and previously caused repeated-call complexity in Lab 4. The first-pass lab remained intentionally bounded and isolated.

## Q: Why stop using `test_tool.py` for the final self-correction proof?

To isolate the concept. Tool selection, state transitions, approvals, and multi-step orchestration were obscuring whether evaluator feedback could actually correct an LLM response.

## Q: `answer_once()` returns a string. Why did `real_evaluator()` fail with `TypeError: string indices must be integers`?

`real_evaluator()` expected the dictionary returned by `run_request()` and tried to access `result["state"]`. `answer_once()` returns plain text, so a separate `answer_evaluator()` was required.

## Q: Why did the simple `Return exactly the word SAFE` test pass immediately?

Because the original prompt already contained the exact formatting rule. That demonstrated compliance but not correction.

## Q: What caused the second attempt to return exactly `SAFE` after the first attempt was verbose?

The evaluator produced the specific feedback `Expected exactly 'SAFE'...`, and `answer_once()` appended that feedback to the model input for attempt 2. The model then adjusted its output to satisfy the explicit requirement.

## Q: Does the retry controller itself know how to fix the answer?

No. It enforces attempt limits and transports feedback. The evaluator determines what failed, and the LLM decides how to respond to that feedback.

---

# Security / Reliability Implications

- Retry must be bounded. An LLM should not autonomously loop until it gets a desired answer.
- Evaluation should be deterministic where possible.
- Feedback should be explicit enough to describe the failed requirement without granting the model new authority.
- Ground truth must be correct; a bad evaluator can push a model toward an unjustified action.
- High-risk actions still require deterministic policy and approval boundaries from earlier labs. Retry feedback is not authorization.
- Attempt inputs, outputs, and evaluator feedback should be observable for debugging and later auditing.
- Multi-step agent correction is more complex than single-answer correction and should be designed separately rather than hidden inside an unbounded loop.

---

# Demonstrated vs. Not Yet Demonstrated

## Demonstrated

- Fixed retry budget with `MAX_ATTEMPTS`.
- Deterministic retry ownership in Python.
- Evaluator returning `(passed, feedback)`.
- Feedback carried to the next attempt.
- Specific fake correction behavior.
- Bounded failure path.
- Real LLM response correction based on evaluator feedback.
- Real LLM hard-stop behavior.
- Logging exact inputs, outputs, evaluator decisions, and feedback.
- Recognition and diagnosis of an existing multi-tool orchestration limitation.
- Recognition that incorrect evaluation ground truth can create unsafe or invalid expectations.

## Not yet demonstrated

- Independent design of a production retry architecture.
- Multi-step tool self-correction across repeated tool calls.
- Persistent retry state across process restarts.
- Retry backoff, budgets, token/cost limits, or time limits.
- Statistical evaluation of correction success rates.
- CI integration.
- Semantic or model-based grading.
- Escalation to a human review queue after terminal retry failure.

---

# Strict Progress Assessment

**Self-Correction / Bounded Retry: 2.0 → 3.0**

Reason: a real bounded retry controller was implemented and tested with both fake and real LLM paths. The real LLM received deterministic failure feedback, changed its second response, passed evaluation, and also demonstrated a hard stop when success was impossible.

No other score changes are justified. Evaluation/Rubrics was reused from Lab 6 rather than substantially expanded. Agent orchestration was explored but not improved; instead, a limitation was identified and intentionally deferred. The implementation remained guided and small-scale.

---

## Final Mental Model

```text
LLM attempt
    ↓
deterministic evaluator
    ↓
PASS → finish
    ↓ FAIL
specific feedback
    ↓
Python checks retry budget
    ↓
next LLM attempt receives feedback
    ↓
PASS → finish
FAIL at limit → stop/escalate
```

**Key principle:** self-correction is not an unbounded LLM loop. The model may use feedback to improve an answer, but deterministic code controls whether another attempt is allowed.