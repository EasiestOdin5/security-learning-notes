# Security Tool Engineering

Hands-on Python and software engineering practice using security investigation problems.

## Purpose
Develop independent implementation skills: requirements, data structures, functions, validation, error handling, debugging, automated tests, and maintainable tooling. The initial project is a local AWS CloudTrail JSON investigation utility. The project will grow from a local parser to indexed investigations and, later, incremental processing and boto3 ingestion.

## Checkpoints
- [2026-10-11 — Python implementation baseline and CloudTrail parser](2026-10-11-python-cloudtrail-checkpoint.md)

## Files
- [cloudtrail_parser.py](cloudtrail_parser.py): a reference snapshot reconstructed from the learner's latest working draft in the conversation. **Not independently executed against the local CloudTrail file.** No raw logs or sensitive event data are committed.

## Working rules
1. Learner writes implementation first; assistant reviews as a code reviewer.
2. Keep CloudTrail evidence read-only and local; never commit real event history containing identifiers or secrets.
3. Distinguish concept familiarity from independent implementation and measured tests.
4. Run code locally and record actual test results before claiming completion.
5. Track Python/tool engineering separately from the existing AWS security competency matrix.
6. Next stage: implement `index_events(data)`, then verify it with small deterministic tests and the local 20,000+ record dataset.
