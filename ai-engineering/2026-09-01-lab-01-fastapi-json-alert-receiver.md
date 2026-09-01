# AI Engineering Lab 1 — FastAPI JSON Alert Receiver

**Date:** September 1, 2026  
**Status:** Completed  
**AI component:** None intentionally — this lab establishes the deterministic boundary before an LLM is introduced.

---

## Goal

Build and containerize a small API that accepts security-alert JSON, validates it deterministically, and rejects malformed input before any future agent or LLM logic sees it.

```text
JSON client
    ↓
Uvicorn
    ↓
FastAPI
    ↓
Pydantic validation
    ↓
receive_alert()
    ↓
JSON response
```

This becomes the ingestion boundary for later labs:

```text
External alert → deterministic validation → LLM/agent → tools → policy gates
```

---

## Environment Setup

Created a project and virtual environment:

```powershell
mkdir ai-agent-lab
cd ai-agent-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installed the web framework and ASGI server:

```powershell
pip install fastapi uvicorn
pip show fastapi
pip show uvicorn
```

---

## Initial FastAPI Application

Started with a minimal endpoint:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
```

Started the service with:

```powershell
uvicorn main:app --reload
```

Confirmed `http://127.0.0.1:8000` returned:

```json
{"status":"ok"}
```

FastAPI automatically exposed interactive API documentation at `/docs` and its OpenAPI schema at `/openapi.json`.

---

## Alert Schema and POST Endpoint

Added a Pydantic model and `POST /alert` endpoint.

Final core model:

```python
from datetime import datetime
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, IPvAnyAddress

app = FastAPI()

class Alert(BaseModel):
    alert_type: str
    source_ip: IPvAnyAddress
    severity: Literal["low", "medium", "high", "critical"]
    timestamp: datetime

@app.post("/alert")
def receive_alert(alert: Alert):
    return {"received": alert}
```

A valid alert was accepted and returned by the handler.

Example:

```json
{
  "alert_type": "suspicious_login",
  "source_ip": "8.8.8.8",
  "severity": "high",
  "timestamp": "2026-09-01T15:30:00Z"
}
```

---

## Validation Tests

### Missing required field

Removed `severity` from the request.

FastAPI/Pydantic rejected the request before `receive_alert()` ran with HTTP `422 Unprocessable Entity` and identified `severity` as required.

### Invalid severity

Changed severity to:

```json
"severity": "urgent"
```

The `Literal` constraint rejected it because only these values are allowed:

```text
low | medium | high | critical
```

### Invalid IP address

Changed source IP to:

```json
"source_ip": "not-an-ip"
```

`IPvAnyAddress` rejected it as neither a valid IPv4 nor IPv6 address.

### Invalid timestamp

The `datetime` field accepted an ISO-8601 timestamp such as:

```text
2026-09-01T15:30:00Z
```

and rejected malformed date/time input.

---

## Dockerization

Created a `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir fastapi uvicorn

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Built the image:

```powershell
docker build -t ai-alert-api .
```

Ran it:

```powershell
docker run --rm -p 8000:8000 ai-alert-api
```

With the host Uvicorn process stopped, `/docs` and `POST /alert` continued to work, proving the application was being served entirely from the Docker container.

---

## Troubleshooting

### Docker could not find the Dockerfile

Initial build failed with:

```text
failed to read dockerfile: open Dockerfile: no such file or directory
```

Cause: Windows had saved the file with a `.txt` extension. Renaming it exactly to `Dockerfile` fixed the build.

### `/openapi.json` Internal Server Error

A temporary `/openapi.json` error appeared while modifying the Pydantic model. After correcting/reloading the current model, the documentation and schema worked normally. The exact exception was not captured, so no unsupported root cause is assigned.

### Source IP field during timestamp edit

One intermediate code snippet accidentally failed to preserve the intended `source_ip: IPvAnyAddress` declaration. Restoring the field and keeping the complete model resolved the inconsistency; timestamp validation then worked as expected.

---

# Questions and Answers

## Is port 8000 chosen by FastAPI or Uvicorn?

`8000` is Uvicorn's default port. FastAPI defines the application; Uvicorn is the server process listening on the port. The port can be changed, for example with `uvicorn main:app --port 9000`.

## What are the roles of FastAPI and Uvicorn?

FastAPI implements application behavior such as routes, request validation, schemas, and responses. Uvicorn accepts network requests and hosts the ASGI application.

```text
client → Uvicorn → FastAPI application → handler → response
```

## Is Uvicorn only for FastAPI?

No. Uvicorn is a general ASGI server and can host other ASGI-compatible Python applications.

## Does Uvicorn need to understand FastAPI's implementation?

No. It interacts with the application through the ASGI interface. It does not need to understand FastAPI decorators, Pydantic models, or routing internals.

## What is ASGI?

ASGI means **Asynchronous Server Gateway Interface**. It is the standard contract between an ASGI web server and the Python web application it hosts.

## Is `@app.get("/")` ASGI?

No. That is FastAPI-specific routing syntax. FastAPI uses its routes internally and exposes the complete `app` object through the ASGI contract.

## What does `uvicorn main:app` mean?

Uvicorn imports the Python module `main`, obtains the Python object stored in the variable `app`, and serves that object as an ASGI application.

## Does Uvicorn see a binary version of `app`?

No. It gets the actual Python object in memory after importing the module.

## Does Uvicorn care about the rest of `main.py`?

It imports the module so Python can construct `app`, but Uvicorn's runtime interaction is with the resulting `app` object through ASGI rather than with the implementation details of the source file.

## Are these beginner questions?

The FastAPI/Uvicorn/ASGI material is beginner backend-web material. The questions focused on abstraction boundaries—server versus framework versus interface—which is useful groundwork for later AI-agent architecture.

## Are fields in a Pydantic model required by default?

Fields without a default value are required. For example:

```python
class Alert(BaseModel):
    alert_type: str
    source_ip: str
    severity: str
```

requires all three fields. An optional field can be declared with a default such as `severity: str | None = None`.

## Is Pydantic only checking whether parameters exist?

No. It can enforce presence, types, allowed literal values, IP-address syntax, date/time structure, ranges, and other constraints.

## Will Pydantic be useful as a gate for LLM output?

Yes. Future LLM output can be forced through a Pydantic schema before application code trusts it. Schema validation can reject malformed structure or values, but separate policy/authorization code must still decide whether an otherwise valid requested action is permitted.

## What does "retry the model" mean?

It means making another LLM API call when an output is invalid, usually including validation feedback and requesting a corrected result. Retries should be bounded—for example, no more than two retries—so the agent cannot loop indefinitely.

---

## Security / Agent Engineering Lessons

1. Untrusted external data should hit deterministic validation before an LLM.
2. Schema-valid data is not automatically authorized or safe; validation and policy are separate controls.
3. The same pattern can later be used on LLM output: `LLM → schema validation → policy gate → execution`.
4. Framework, runtime/server, and interface boundaries should remain explicit because agent systems add additional boundaries such as model, orchestrator, tool executor, and policy engine.
5. Containerization gives the future agent service a reproducible deployment boundary that can later move into Kubernetes.

---

## Demonstrated Evidence

Completed hands-on:

- Created and activated a Python virtual environment.
- Installed and ran FastAPI and Uvicorn.
- Created GET and POST endpoints.
- Used FastAPI's generated `/docs` interface.
- Defined a Pydantic request model.
- Demonstrated rejection of a missing required field.
- Restricted severity with `Literal`.
- Validated IPv4/IPv6 syntax with `IPvAnyAddress`.
- Validated timestamps with `datetime`.
- Distinguished FastAPI, Uvicorn, ASGI, the source module, and the in-memory `app` object.
- Built a Docker image for the service.
- Diagnosed a Windows `Dockerfile.txt` naming problem.
- Ran the service entirely from the container.
- Verified `POST /alert` from the containerized deployment.

## What Was Not Demonstrated Yet

- LLM API integration.
- LLM structured output.
- Tool/function calling.
- Agent orchestration.
- Model-based evaluation.
- Retry implementation.
- RAG or persistent agent memory.

Those remain future labs.