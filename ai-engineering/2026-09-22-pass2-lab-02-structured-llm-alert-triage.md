# Pass 2 — Lab 2: Structured LLM Alert Triage

**Date:** September 22, 2026  
**Status:** Completed  
**Pass:** Pass 2 — independent implementation from a guided design

---

## Goal and Architecture

Rebuild the direct OpenAI triage path on top of the Pass 2 FastAPI receiver, keeping **model output** separate from **deterministic application decisions**.

```text
JSON {"message": "..."}
    → FastAPI /triage and Pydantic TriageRequest
    → OpenAI Responses API parse()
    → Pydantic AlertTriage output
    → application confidence gate
    → HTTP 200: {"result": model assessment, "needs_review": bool}
    └ on OpenAI SDK error → HTTP 503 controlled error
```

This lab does not implement investigation tools, an approval workflow, persistence, or evaluation/calibration of model confidence.

---

## Implemented Shape

The request model contained `message: str`. The structured response model used:

- `classification`: `benign`, `suspicious`, `malicious`, `irrelevant`;
- `severity`: `low`, `medium`, `high`, `critical`;
- `needs_investigation: bool`;
- `confidence: float = Field(..., ge=0.0, le=1.0)`;
- `reason: str = Field(..., min_length=1)`.

The enum values and numeric/length constraints validate the *shape and allowed values* of an assessment; they do not establish that the security judgment is correct.

Compact final endpoint shape (imports and schema definitions omitted):

```python
@app.post("/triage")
def triage(request: TriageRequest):
    try:
        response = client.responses.parse(
            model="gpt-5.6-luna",
            input=request.message,
            text_format=AlertTriage
        )
    except openai.OpenAIError:
        raise fastapi.HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "reason": "llm_api_failure",
                "message": "Unable to complete triage."
            }
        )

    needs_review = response.output_parsed.confidence < 0.70
    return {
        "result": response.output_parsed,
        "needs_review": needs_review
    }
```

The threshold `0.70` is an exercise rule, **not an empirically calibrated confidence cutoff**.

---

## Demonstrated Tests

1. A login alert about Alice with 12 failed logins, one successful login from `8.8.8.8`, an unfamiliar device, and a 03:15 login yielded a structured suspicious/high/investigate assessment in an observed test.
2. Nonsecurity messages were tried; an explicit `irrelevant` category was added instead of treating unrelated content as `benign`.
3. The `needs_review` comparison was tested deterministically with temporary confidence values `0.45` (true) and `0.90` (false), then restored to use `response.output_parsed.confidence`. This verifies the comparison logic, not the model's confidence calibration.
4. A deliberately invalid API key was supplied to a rebuilt Docker image. The user confirmed HTTP **503**, validating error translation rather than a misleading HTTP 200.
5. After restoring the valid key, the user confirmed a successful request returned HTTP **200** with `result` and `needs_review`.

---

## Troubleshooting

- `client.responses.create(..., text_format=AlertTriage)` was corrected to `client.responses.parse(..., text_format=AlertTriage)` for the structured parse route.
- An endpoint returning no value serialized as JSON `null`; the endpoint must return the response data explicitly.
- The container initially lacked `openai`; local virtual-environment packages are not automatically available in the image.
- The Dockerfile mistakenly installed `openapi`, corrected to `openai`.
- A key-setting attempt used PowerShell's `$env:OPENAI_API_KEY` syntax in `cmd.exe`, passing invalid credentials. `docker run -e OPENAI_API_KEY` copies an already-set host environment variable; `-e OPENAI_API_KEY=value` supplies a literal value. Avoid embedding real keys in source, the Dockerfile, or shared notes.
- An attempt to assign `response.output_parsed.needs_review = True` would add an undeclared attribute to a Pydantic model. The gate was correctly kept as a separate Python Boolean.
- Initially, catching `OpenAIError` returned a JSON error dictionary with HTTP 200. This was corrected to `HTTPException(status_code=503, detail=...)`.
- Code changes in `main.py` require `docker build` before `docker run` for an image that copied `main.py` during build.

---

## Questions and Answers

### How is `needs_investigation` different from `needs_review`?

`needs_investigation` is the model's recommendation about the underlying alert. `needs_review` is the application's independent policy decision about whether the **model assessment** needs review, such as when confidence is below 0.70. An alert can have `needs_investigation: false` but `needs_review: true`.

### Why put `needs_review` outside `result`?

Either documented JSON layout is possible. Keeping it outside distinguishes original LLM fields from deterministic policy output and supports auditing. To nest the gate inside `result`, explicitly construct a new dictionary rather than dynamically mutating `AlertTriage`.

### How can I reproduce confidence below 0.70?

Do not rely on a prompt to force an exact model confidence. Temporarily compare a controlled value, e.g. `0.45 < 0.70` and `0.90 < 0.70`, then restore the model-derived expression.

### Is it okay for success and failure JSON to differ?

Yes. Successful HTTP 200 responses provide `result` and `needs_review`; a FastAPI `HTTPException` produces an error under `detail`. Clients should check the HTTP status before consuming success fields.

### Why raise `HTTPException` instead of returning JSON describing an error?

Returning a dictionary defaults to HTTP 200. A custom client could interpret an error field, but generic HTTP tools, monitoring, gateways, and retry logic often use status codes. HTTP 503 communicates failure at the protocol level, with JSON explaining the reason.

### Is `OpenAIError` strictly an HTTP error?

No. It is an SDK exception family that also includes connection and timeout failures without an HTTP response. The application translates an upstream SDK failure into its own HTTP response. A production service would likely distinguish authentication/configuration, rate limits, transient outages, and timeouts rather than mapping all cases to 503.

### Why add `irrelevant` instead of mapping nonsecurity text to benign?

`benign` is an assessment within the security domain; `irrelevant` marks content outside the triage task. A larger application could have a dedicated upstream relevance classifier, but that adds cost, latency, and false-negative risk. This small lab retained one structured model pass.

### Where does Docker store the image?

In Docker-managed local filesystem storage, generally a WSL 2 virtual disk under Docker Desktop on this Windows setup, not in the project directory. `docker image ls` lists images; `docker system df` shows usage. The Docker image remains after a `docker run --rm` container exits.

### How do I transfer the image elsewhere?

```powershell
docker save -o ai-agent-lab-pass2.tar ai-agent-lab-pass2
docker load -i ai-agent-lab-pass2.tar
docker run --rm -p 8000:8000 -e OPENAI_API_KEY ai-agent-lab-pass2
```

`docker save`/`docker load` transfer an image file; `docker push`/`docker pull` use a registry. Set credentials independently on the destination computer. These commands were discussed; transfer to a second computer was **not demonstrated**.

---

## Security and Engineering Implications

- LLM output validity is not judgment accuracy; future evaluation must measure misclassifications and confidence behavior.
- An unrelated message is not a benign security finding.
- Keep model assessment separate from application policy. Do not let a model mark its own judgment as exempt from review.
- Do not expose raw SDK exceptions or credentials in API error payloads.
- Check status codes, not only JSON text, to detect failed requests.
- Invalid-key test supports exception handling only; it does not show every upstream failure behaves identically.
- Docker image portability does not include runtime secrets unless they were improperly baked into the image.

---

## Independent vs Guided

**Independently reconstructed / exercised:** response schema and enums, structured `parse()` integration after correction, irrelevant classification, confidence-gate Boolean, Docker build/run retesting, and successful/failed API calls.

**Guided or corrected:** Responses API `parse()` method, Pydantic field constraints and undeclared-attribute issue, the distinction between investigation and review, suggestion to use `HTTPException` with 503, and the invalid-key/controlled-confidence test methods. Broader modular relevance design and Docker image transfer were discussed, not implemented as extra lab features.

---

## Conservative Score Changes

| Skill area | Before | After | Evidence |
|---|---:|---:|---|
| LLM API Fundamentals | 3.0 | 3.25 | Rebuilt structured Responses API call, integrated it with FastAPI, and tested error/success paths |
| Structured Outputs / Schemas | 3.75 | 4.0 | Rebuilt constrained Pydantic LLM response and tested security versus irrelevant classifications |
| Deterministic Gates / Policy Controls | 5.25 | 5.5 | Implemented and tested a separate deterministic low-confidence review decision |

No deployment score change for repeated minimal Docker build/run; image export was explained rather than performed. No agent-security or evaluation score change based on discussion alone.

**Next:** Pass 2 Lab 3 — Read-Only Investigation Tools.
