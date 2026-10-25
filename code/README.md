# Deletion audit agent

Runnable local prototype with a deterministic audit core and local screenshot OCR. No API key or paid model service is required. A hosted API and the proposed interactive frontend are not implemented; the run generates a static readable case report.

## Setup

Use Python 3.11+ and install `pip install -r code/requirements.txt`. On Windows, screenshots use the operating-system Windows.Media.Ocr engine through PowerShell. On Linux/macOS, install the `tesseract` command. Windows OCR must be allowed to read the supplied files; the Codex sandbox may require a locally approved extraction run. Do not disable machine-wide security settings.

Run from the repository root, with the original participant dataset present:

```text
python code/main.py
python code/main.py validate
python code/evaluation/main.py
python -m unittest discover -s code/evaluation -p test_*.py
```

Optional paths: `python code/main.py audit --dataset dataset --cases deletion_requests.csv --output output.csv`.

The audit never reads sample_output.csv. Evaluation separately runs sample requests and then compares them with public expected outputs. Sample cases with insufficient grounded evidence remain unresolved in evaluation rather than borrowing the expected answer.

## Outputs

- Root `output.csv`: exact challenge schema and one row per supplied request.
- `.runtime/audit_report.html`: static case report with ordered actions and checks.
- `.runtime/observations.sqlite`: source registry and provenance-linked observations.
- `.runtime/ingestion.json`: file inspection outcomes and extraction counts.
- `.runtime/run_summary.json`: final-run counts, diagnostics and usage.
- `.runtime/sample_metrics.json`: sample metrics and precise step mismatches.

Caches are keyed by screenshot content hash and extraction version. Windows screenshots use text and spatial-layout passes; row-local identifiers avoid cross-customer contamination. They are derived evidence text, not answers, and are excluded from code.zip. A clean run reads the images again. Source files remain unchanged. SQL is loaded into an isolated in-memory connection with restricted authorizer and work limits.

## Implementation and limitations

The pipeline reads all supplied formats, expands current/historical identity keys, correlates trace events, distinguishes readback from operation claims, checks snapshot/replica scopes, loads required treatments from deletion_rules.csv, and serializes the exact operation order. Sources are cited using participant-visible IDs. Future actions and checks for incomplete cases have empty citations.

Ownership discovery may use later artifacts; audit-time state and citations remain restricted to the cutoff. Worker events inside the intake/report window supply ownership candidates, subject to explicit-owner and overlapping-request guards. Both supplied request CSVs provide intake-window metadata; no expected answers are read by inference. Existing resources from prior deletion episodes are excluded unless observed or touched in the current request episode. Incomplete-case verification covers all linked resources, including future checks for resources whose audit-time state is unknown. Complete cases still require eligible state evidence.

This is an initial implementation, not a fully validated production system. Intent currently uses multilingual rules rather than an LLM. Windows screenshot extraction uses spatial OCR and generic resource/alias matching; other operating systems currently use text OCR. Identity alias matching does not yet fully enforce historical availability intervals. Supplied policy conditions are not fully generalized beyond the observed categories. Some primary-account and anonymized-resource ownership links cannot yet be established; missing required verification steps reduce sample exact-match accuracy. A clean format check is not a semantic correctness guarantee. Consult evaluation/evaluation_report.md and evaluation/evidence_gaps.md for measured results before using predictions.

The design documents describe a broader target architecture. Unimplemented portions must not be represented as completed functionality.

## Experimental cross-case ownership elimination

`code/audit/ownership.py` builds type-specific worker candidates over both supplied request sets, locks direct owners and propagates uncontested singletons without ID/order/nearness tie-breaking. Overlapping intake windows for the same subject are treated as one episode. Remaining choices and contested singletons are recorded as unresolved.

This strict replacement is **disabled by default**: public-sample precision stayed at 100%, but two previously correct cases regressed. The final output retains the existing baseline, including its prior completion-boundary matching. Evaluation labels are never passed to the ownership solver or audit engine. Trials do not overwrite final predictions or default evaluation metrics.

```text
python code/evaluation/main.py --capture-baseline
python code/evaluation/main.py --cross-case-elimination
python code/evaluation/main.py --cross-case-elimination --extended-window
python code/evaluation/main.py --cross-case-elimination --supplemental
python code/evaluation/main.py --cross-case-elimination --extended-window --supplemental
python code/evaluation/main.py
```

The extended trial uses `[requested_at, audit_at]` for ownership candidates; post-report events must survive singleton elimination. State and citations still require evidence available by audit_at. It breaks a third previously correct sample. Supplemental trials preserve the baseline but recover no additional steps. Final exact-row accuracy remains 46.875%, step precision 100%, and step recall 88.601%. No improvement in exact-row accuracy is claimed.

Evaluation writes `evaluation/ownership_trace.md` (full competing request windows, grounding citations and propagation steps), `evaluation/evidence_gaps.md` (all remaining missing steps and candidate sets), and `evaluation/media_audit.md` (11 screenshots and 4 PDFs). Detailed JSON traces are also available in `.runtime/ownership_trace_original.json` and `.runtime/ownership_trace_extended.json`. Aggregate measured experiment history is kept only under evaluation; it is never imported by prediction code. All workflows leave log.txt untouched.

After regenerating and validating output, run `python code/package_submission.py` to rebuild code.zip. The package includes the evaluation reports and excludes the corpus, caches, environments and secrets.
