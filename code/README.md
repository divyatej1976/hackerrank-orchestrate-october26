# Ghost Data Still Exists — deletion audit agent

Audits every request in `dataset/deletion_requests.csv` and writes `output.csv`
(`case_id,deletion_status,steps_json`). For each request it decides whether
deletion was authorized, reconstructs the subject's current and historical
identifiers, reads all evidence formats, rebuilds each resource's state at
`audit_at`, applies `deletion_rules.csv`, and emits ordered findings,
remediation and verification steps.

## Results (32 public samples, `code/evaluation/evaluation_report.md`)

| Metric | Result |
|---|---:|
| Status accuracy | 100.0% |
| Exact-row / sequence accuracy | 65.6% |
| Step precision | 100.0% |
| Step recall | 93.8% |
| Field accuracy | 92.2% |

51 authored regression tests cover the audit and Groq intent client. The full
run produces 518 contract-valid rows. Cold Groq runs are sequential and take
longer than rules-only/cache-warm runs. Measured usage is in code/evaluation/usage_report.md.

## Setup and run

Python 3.11+. Extract code.zip into a working folder and copy the supplied
`dataset/` beside `code/` (not inside it):

```text
working-folder/
  code/
    main.py
    requirements.txt
    evaluation/   # reports: evaluation_report.md, usage_report.md
  dataset/
    deletion_requests.csv
    evidence/
```

Run these commands from `working-folder/`. Dependencies are installed into
the Python environment used for the run:

```text
python -m pip install -r code/requirements.txt
python code/main.py              # audit all requests -> output.csv
python code/main.py validate     # re-check output.csv against the contract
python code/evaluation/main.py   # sample metrics + tests -> evaluation/*.md
python code/package_submission.py
```

The Python dependencies are pypdf and Pillow. On Windows, use Windows 10/11,
Windows PowerShell (`powershell.exe`) and an installed OCR language, such as
English. Screenshots are read with Windows.Media.Ocr through the included
`extract_windows_ocr.ps1`. Run from a normal local PowerShell session with
permission to read the evidence and create files in the working folder. A
restricted agent sandbox may block WinRT OCR even when Python dependencies
are installed; use the approved local execution environment in that case.

On Linux/macOS, install the separate `tesseract` executable and its English
language data and make it available on PATH; pip does not install this system
dependency. Those platforms currently use text OCR without Windows spatial
layout extraction, and were not validated by this Windows clean-run test. OCR
text is cached under `.runtime/ocr/` by image hash, so reruns are fast and
deterministic. For live Groq intent classification, supply `GROQ_API_KEY` only
through the process environment. Never paste the key into chat, commands,
source files, `.env`, reports or logs. There is no dotenv loader. No API key
is needed for the default rules-authoritative audit to finish. Missing keys
or failed/invalid responses fall back to the original rules.

On Windows, set the variable in the environment of the terminal/application
that launches the agent; already-running applications must restart to inherit
changed user environment variables. No command prints or copies the key.

The default policy is `audit/intent_policy.json`. `--intent-mode shadow` keeps
rules authoritative and records the LLM as a second opinion; `--intent-mode rules`
disables model calls. The evaluator downgrades a regressing primary trial to
shadow, regenerates/validates full predictions, and lists every changed
NOT_APPLICABLE decision and its request text in intent_classification_report.md.
No public expected labels are passed into inference.

The validated default is now **shadow**. The primary GPT-OSS trial incorrectly
treated four public follow-up deletion/audit requests as NOT_APPLICABLE
(case_06, case_21, case_25, case_27), lowering sample status accuracy to 87.5%.
Rules remain authoritative, restoring the table above. The model agrees with
rules on 28/32 public requests (87.5%); the reports retain every disagreement
and the four original request texts. The 518-row NOT_APPLICABLE set remains 10.

## How it works

| Stage | Code | What it does |
|---|---|---|
| Intent | `audit/core.py` `deletion_intent`, `audit/llm.py`, `prompts/intent_classification.md` | Rules are authoritative in the default shadow mode. Groq openai/gpt-oss-120b returns a JSON second opinion at temperature 0; explicit refusal always wins. Disagreements retain case diagnostics. Model/prompt/text-hashed local response caching separates live and reused token usage. |
| Identity | `IdentityIndex` | Resolves the request email (any case, current or historical) to a `user_id` and expands every email, phone and hash from `user_identities.csv` + `user_audit_log.csv`. |
| Ingestion | `audit/ingestion.py`, `audit/layout.py` | Parses JSON, logs (several wrapper formats), SQL snapshots (isolated in-memory SQLite), text, PDFs (`pypdf`) and screenshots (spatial OCR keeps table rows together) into time-stamped observations with their `file_id`. |
| Ownership | `AuditEngine.workflow_resources` | Uses direct identifiers, readback lookup keys and resource references, plus workflow-window/report-result ownership heuristics. A primary-account slot fills the account when exactly one status-consistent worker candidate remains after elimination. State still requires eligible evidence. |
| State | `_state` | Picks the latest evidence available at or before `audit_at`; workflow statuses and operation results are treated as claims, never proof. Replica and snapshot scopes are checked separately. |
| Policy and plan | `audit` | Applies DELETE / REDACT / ANONYMIZE / RETAIN / tombstone rules, reports active flows and restore risks, disables flows and blocks restores before dependent records, and orders steps by the spec's operation table, then `system_id`, then `resource_id`. |
| Validation | `validate` | Fails the run on any contract break: row set, status values, empty `[]` for NOT_APPLICABLE, step order and numbering, operation/state pairs, citations dated after `audit_at`, or citations on future steps. |

Unresolved ownership can leave required steps out. The current heuristics
achieve 100% step precision on public samples, but that measurement does not
establish complete coverage or hidden-dataset accuracy.

## Clean extracted-package test

The Windows clean-run test extracted code.zip into a new folder, copied only
the supplied dataset beside code, and started with no `.runtime` directory
and no `GROQ_API_KEY` in the child process. Both `python code/main.py` and
`python code/main.py validate` succeeded. The run made 22 fresh local OCR calls
with zero cache hits and produced 518 sorted, contract-valid rows identical
to the current output. The audit took about 49 seconds on the tested host.
See `code/evaluation/clean_run_report.md` for environment details and commands.

The test used an existing Python environment with the requirements installed;
it was a clean application/cache test, not a fresh OS or dependency installation.
All reports live in `code/evaluation/`; CLI runs update them there.

## Files

- `main.py` — CLI entry point.
- `audit/` — engine (`core.py`), ingestion, OCR layout, ownership experiments, reporting.
- `evaluation/` — evaluator, regression tests, and the required reports
  (`evaluation_report.md`, `usage_report.md`), plus `evidence_gaps.md` and `media_audit.md`.
- `prompts/intent_classification.md` — multilingual intent system prompt.
- `SYSTEM_ARCHITECTURE.md` — the implemented CLI pipeline, data flow and storage.
- `PROMPT_ENGINEERING.md` — the implemented intent prompt, authority rules, cache and usage accounting.

Sample labels (`sample_output.csv`) are read only by `evaluation/`, never by
the audit engine.

Groq calls use the standard library only, a 20-second timeout and at most one
retry for HTTP 429/5xx. A named application User-Agent avoids urllib's default
agent rejection. HTTP 401/403/404 stops further live requests in that client;
remaining texts fall back to rules, and a new run retries provider access.
Requests and retries are sequential. The in-process cache
prevents repeated ownership lookups from inflating token counts. Local response
caches contain only parsed answers, model name and usage, never credentials or
headers, and are excluded from code.zip. Mocked test tokens are excluded from
usage reports. Cost assumptions are centralized in audit/llm.py: $0.15 input/$0.60 output per
million tokens, checked against Groq's GPT-OSS 120B model documentation on
2026-10-25. Estimates exclude account discounts and provider prompt-cache
reductions; recheck [Groq pricing](https://groq.com/pricing).

The user authorized openai/gpt-oss-120b after the requested Llama 3.3 model
returned model_not_found and was absent from the account's model list. The client
uses low reasoning effort, a 512-token completion limit and JSON object mode;
reasoning text is excluded from the response and never persisted.
