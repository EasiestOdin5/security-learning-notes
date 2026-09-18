# Pass 2 — Lab 1: FastAPI JSON Alert Receiver

**Date:** September 18, 2026  
**Status:** Completed  
**Pass:** Pass 2 — independent implementation from a guided design

---

## Goal

Rebuild Lab 1 without supplied implementation code. The design target was:

```text
JSON alert
→ FastAPI endpoint
→ Pydantic validation
→ valid request accepted
→ invalid request rejected
→ containerized with Docker
```

The purpose of Pass 2 is to separate implementation skill from system-design skill: the architecture is supplied, but the code is written and debugged independently.

---

## Final Application Shape

The application implemented:

- FastAPI application creation;
- `GET /` basic response;
- `GET /health` health endpoint;
- `POST /alerts` alert receiver;
- Pydantic `Alert` model;
- IP validation with `IPvAnyAddress`;
- non-empty username validation with `Field(..., min_length=1)`;
- severity validation with a Python `Enum`;
- valid and invalid request testing through FastAPI docs;
- Docker image build and container execution;
- verification that the containerized API behaved the same as the local API.

The compact model was:

```python
class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Alert(BaseModel):
    source_ip: IPvAnyAddress
    destination_ip: IPvAnyAddress
    username: str = Field(..., min_length=1)
    severity: Severity
```

The endpoint accepted one validated `Alert` object rather than four unrelated parameters.

---

## Docker

A minimal Dockerfile was independently written using:

- `python:3.13-slim`;
- `WORKDIR /app`;
- copy of `main.py`;
- pip installation of FastAPI, Uvicorn, and Pydantic;
- Uvicorn bound to `0.0.0.0:8000`.

A correction was needed because `Enum` was initially added to the pip install list. `enum` is part of the Python standard library and does not require pip installation.

The image was built, run, and the containerized `/health`, `/docs`, and `/alerts` behavior was verified.

---

## Tests Performed

Valid alert input was accepted.

Invalid cases were deliberately tested, including:

- malformed IP such as `10.20.30.400`;
- invalid severity such as `low2`;
- missing username;
- empty username.

Pydantic/FastAPI returned structured validation errors before the endpoint logic ran.

---

## Questions and Answers

### Is the API receiving four values or JSON?

The four alert values are transmitted together in the HTTP request body as JSON. FastAPI passes the request body to Pydantic, which constructs one `Alert` object.

### When values are entered through `/docs`, are they sent as JSON?

Yes. FastAPI's Swagger UI sends the entered request body as JSON to the endpoint.

### What does the API do besides checking the four values?

For this lab, very little by design. It receives an alert, validates its schema and field constraints, rejects invalid data, and returns a simple confirmation for valid data. No LLM, persistence, tool calling, or investigation logic is part of Lab 1.

### How does Pydantic know how to validate `severity`?

Because `Alert` inherits from `BaseModel`. Pydantic inspects each annotated field. Since `severity: Severity`, it validates the value against the members of the `Severity` enum.

### Is everything inside a `BaseModel` checked?

Pydantic validates each declared field according to its annotation and constraints. In this lab:

```text
IPvAnyAddress → IP format
str + Field   → string and length constraint
Severity      → enum membership
```

### In a Python interview, should IP validation use Pydantic?

Usually not. A general Python interview would more commonly use the standard-library `ipaddress` module, or require a manual IPv4 validator if the interviewer wants algorithmic reasoning.

### Is manual IPv4 validation reasonable?

Yes, if the exercise requires implementing it manually: exactly four dot-separated numeric parts, no empty parts, and each value in the range 0–255.

### How can standard-library modules be distinguished from external packages?

Standard-library modules ship with Python, for example `enum`, `json`, `ipaddress`, and `datetime`. External packages such as FastAPI, Pydantic, OpenAI, Scapy, and NetworkX generally require pip installation.

### Does `WORKDIR /app` have special meaning?

No. `/app` is an arbitrary absolute directory inside the container filesystem. It becomes the working directory for subsequent Dockerfile instructions and the runtime command.

### Is `/app` at the container filesystem root?

Yes:

```text
/
└── app/
    └── main.py
```

### Are Dockerfile commands executed as root?

By default, commonly yes unless the base image or Dockerfile switches users with `USER`. Build steps such as package installation often run as root, and the runtime command also uses the current configured image user.

---

## What Was Independent vs Guided

### Independent

- wrote the FastAPI starter application;
- wrote the `Severity` enum;
- wrote the `Alert(BaseModel)` model;
- selected and used `IPvAnyAddress`;
- added the username constraint;
- wrote the `POST /alerts` endpoint;
- tested valid and invalid requests;
- wrote the first Dockerfile attempt;
- built and ran the Docker image;
- verified containerized behavior.

### Guided / refreshed

- overall Lab 1 architecture and requirements;
- reminder that one `Alert` object should represent the JSON body;
- explanation of how `BaseModel` validates enum fields;
- clarification of standard-library vs third-party modules;
- correction that `Enum` should not be installed with pip;
- Docker `WORKDIR` and default-user concepts.

This is stronger evidence than Pass 1 because the implementation was reconstructed rather than copied, but it is not yet independent system design.

---

## Score Changes

| Skill area | Before | After | Reason |
|---|---:|---:|---|
| Structured Outputs / Schemas | 3.5 | 3.75 | Independently rebuilt a typed Pydantic request schema with IP, enum, and field constraints and tested rejection behavior |
| AI Application Deployment | 4.5 | 4.75 | Independently reconstructed the minimal Docker build/run path for the API and verified behavior inside the container |

No other score changes are justified from this lab.

---

## Main Takeaway

The core implementation pattern was successfully reconstructed:

```text
external JSON
→ deterministic typed boundary
→ validated Python object
→ application logic
```

The remaining weakness is recall fluency: several Pass 1 concepts had to be refreshed before implementation. That is exactly what Pass 2 is intended to improve.
