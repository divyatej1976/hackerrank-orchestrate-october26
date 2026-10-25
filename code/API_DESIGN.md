# API and Interface Design

Date: 24 October 2026 · Status: proposed contracts

## Is an HTTP API required?

No. The challenge requires reading local files and producing output.csv. Implement a CLI and typed internal interfaces first. An HTTP API becomes useful for a reviewer workspace or external integration later; it should wrap the same audit engine rather than duplicate its logic.

## MVP CLI proposal

```text
python code/main.py audit --dataset dataset --output output.csv
python code/main.py audit --dataset dataset --cases sample_deletion_requests.csv --output sample_predictions.csv
python code/evaluation/main.py --predictions sample_predictions.csv --expected dataset/sample_output.csv
python code/main.py validate --dataset dataset --output output.csv
```

These commands are proposed, not implemented. Case-file paths are resolved under the selected dataset unless explicitly documented otherwise. The default audit reads deletion_requests.csv. Expected answers are accepted only by evaluation, never the audit command.

Suggested exit codes: `0` successful validated run; `2` input/configuration error; `3` unresolved material evidence; `4` extraction/runtime failure; `5` output validation failure. Diagnostics include the run ID and stage. A failed run preserves the previous final output and does not call it current.

## Internal service interfaces

```text
ingest_dataset(dataset_root, extraction_config) -> DatasetIndex
classify_intent(request, model_config) -> IntentResult
resolve_subject(request, index, cutoff) -> SubjectResolution
investigate(request, subject, index, policy, budget) -> CaseAssessment
plan(assessment) -> CandidateCaseOutput
validate_case(candidate, assessment, source_registry) -> ValidationResult
export_run(validated_cases, destination) -> ExportManifest
```

Inputs/outputs use the typed entities in DATABASE_DESIGN.md. Errors distinguish not found, ambiguous, unsupported format, invalid extraction, insufficient evidence, and contract failure. Empty results are successful only when their scope is explicit.

## Optional HTTP resource design

| Method and path | Purpose | Result |
|---|---|---|
| POST `/v1/audit-runs` | Start an audit using a registered dataset and configuration | 202 with run reference |
| GET `/v1/audit-runs/{run_id}` | Progress, counts, unresolved cases and validation state | 200 |
| GET `/v1/audit-runs/{run_id}/cases` | Paginated case summaries and filters | 200 with opaque cursor |
| GET `/v1/audit-runs/{run_id}/cases/{case_id}` | Verdict, findings, plan, coverage and provenance links | 200 |
| GET `/v1/audit-runs/{run_id}/cases/{case_id}/evidence/{evidence_id}` | Authorized source excerpt/locator | 200; access scoped to case and dataset |
| POST `/v1/audit-runs/{run_id}/retry` | Retry eligible failed work against pinned inputs | 202 with new attempt reference |
| GET `/v1/audit-runs/{run_id}/export` | Download validated CSV | 200, or 409 if not ready |

No remediation-execution endpoint belongs in this version. Request creation accepts a registered dataset ID, not arbitrary filesystem paths or remote URLs. New inputs/configurations create a new run; retry does not silently change the evidence version.

Example creation body:

```json
{
  "dataset_id": "registered_dataset_reference",
  "request_set": "deletion_requests",
  "configuration_id": "pinned_configuration_reference"
}
```

Example unresolved case response:

```json
{
  "case_id": "illustrative_case",
  "processing_state": "review_needed",
  "deletion_status": null,
  "coverage": {"satisfied": 2, "violated": 0, "unresolved": 1},
  "issues": [{"code": "UNREADABLE_EVIDENCE", "evidence_id": "registered_source"}]
}
```

Nullable API verdicts represent unfinished work, not a permitted CSV value. A validated export contains only the three challenge statuses and exact CSV fields.

## Operational and access requirements for a future service

Authenticate callers and authorize dataset/run/case/evidence access independently. In a multi-organization service, enforce tenant scope on every query and object reference. Mask identifiers in list views and provide source detail only to authorized reviewers. Do not expose raw filesystem paths, model prompts containing PII, or secrets in error responses.

Use an idempotency key on run creation, bound to the request payload and caller scope. Return the original run for an identical repeated request and a conflict for key reuse with a different payload. Maintain an audit trail for source access and review actions. Bound request sizes, pagination, work queues and model budgets.

Use structured error responses with `code`, safe `message`, `run_id` when applicable, and `retryable`. Retry transient infrastructure errors with limits; ambiguous evidence is not a transient HTTP error. Cancellation and reviewer overrides require separate contracts before implementation.

## Delivery decision

Build CLI plus internal interfaces for the challenge. Defer HTTP endpoints until a UI/integration is explicitly selected. No hosted database, API server, authentication infrastructure, or production network deployment is required to produce a valid submission.
