# Local OpenRouter HTTP verification

The local simulation exercises `stroytech.openrouter` and `extract_rules` through real urllib HTTP with a synthetic credential. Production keeps its fixed HTTPS host: the verification process temporarily assigns the module endpoint to loopback, restores it afterward, and never replaces the opener. No application restart, cloud upload, deployment, authenticated provider request or paid inference is involved.

## Run

From the repository root, start the server in a dedicated terminal:

```sh
postman simulation run postman/simulations/openrouter.sim.yaml --port 43187 --no-history --output ndjson --verbose > /tmp/stroytech-openrouter.ndjson 2> /tmp/stroytech-openrouter.err
```

Wait for its `listening` event, then run in another terminal:

```sh
python3 scripts/verify_openrouter_http.py
python3 scripts/verify_openrouter_logs.py /tmp/stroytech-openrouter.ndjson
```

Run log verification after the delayed request finishes (1.5 seconds). Stop the simulation with Ctrl-C in its owning terminal. The default mock serves `POST /api/v1/chat/completions`; local-only `/__control/<case>` selects cases, because simulation members ignore per-request mock scenario headers. Tests require exclusive access to this local mock state. Raw request logs stay outside the repository.

## Observed evidence, 2026-11-04

Postman 1.75.0 ran the real urllib client successfully. Both `filter_first` and `extract_first` produced one validated candidate with status `pending`, each making two model calls. The failure scenarios below all raised `ExtractionError`, rather than returning an empty successful list:

| Case | Observed result |
| --- | --- |
| HTTP 401 | API key diagnostic |
| HTTP 402 | Insufficient funds diagnostic |
| HTTP 429 | Rate limit diagnostic |
| HTTP 500 | Service failure diagnostic |
| Missing choices | Malformed response diagnostic |
| Non-JSON model content | Invalid model JSON diagnostic |
| Empty model content | Rejected response |
| 1500ms response delay, 200ms timeout | Network/timeout diagnostic |

Across three verification passes, the log recorded 34 model POSTs: 22 HTTP 200 responses and three each of 401/402/429/500 (the first pass covered nine cases, the final two covered ten). Verbose NDJSON inspection and `verify_openrouter_logs.py` confirmed the actual POST path, `model=mock/model`, one user message, expected source text, `stream=false`, and JSON content type. The handler rejects an incorrect synthetic Bearer token before producing these responses; logs redact Authorization. Transcript checks found no synthetic key. No retry followed the modeled first-stage failures. Timeout logging shows the server eventually produced its response; a timeout does not establish cancellation or absence of provider charges.

## Contract and remaining gaps

This independently written mock models a narrow subset from the official [Chat Completions overview](https://openrouter.ai/docs/api_reference/overview), [authentication](https://openrouter.ai/docs/api_reference/authentication) and [errors](https://openrouter.ai/docs/api_reference/errors-and-debugging) documentation. The application-specific rule JSON is a fixture, not an OpenRouter guarantee. Unsupported routes return 501. The mock does not model streaming, routing, provider retries, billing, real model quality or all response fields.

Authenticated owner lookup was skipped as instructed: this installed CLI does not support `postman status`; earlier provider discovery yielded irrelevant services. No owner-maintained mock was retrieved. CLI 1.75.0 requires the simulation member path to reference `config.yaml` rather than its directory, and the mock manifest includes `version: 1` and a default scenario path.

The context file records contract-backed claims separately from demonstrated caller behavior and unverified real-provider assumptions. Real credentials, permissions, selected-model availability, semantic extraction quality and production TLS behavior still require separate verification. All mock processes started for this verification were stopped afterward.
