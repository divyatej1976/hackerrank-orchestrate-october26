# Accuracy comparison

Public samples only. Expected answers are read exclusively in code/evaluation/. No sample labels or target resource IDs are used by inference.

| Variant | status_accuracy | exact_row_accuracy | sequence_accuracy | step_precision | step_recall | step_f1 | field_accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Before | 96.8750% | 46.8750% | 46.8750% | 100.0000% | 88.6010% | 93.9560% | 86.0844% |
| Strict replacement | 90.6250% | 40.6250% | 40.6250% | 100.0000% | 87.0466% | 93.0748% | 84.5300% |
| Extended replacement | 90.6250% | 37.5000% | 37.5000% | 100.0000% | 86.5285% | 92.7778% | 83.6417% |
| Supplemental strict | 96.8750% | 46.8750% | 46.8750% | 100.0000% | 88.6010% | 93.9560% | 86.0844% |
| Supplemental extended | 96.8750% | 46.8750% | 46.8750% | 100.0000% | 88.6010% | 93.9560% | 86.0844% |
| Final: baseline (account slot disabled) | 96.8750% | 46.8750% | 46.8750% | 100.0000% | 88.6010% | 93.9560% | 86.0844% |

Final previously-correct sample regressions: []. All 15 original exact-correct cases checked. Final matching steps: 171/193; missing: 22; extra: 0.
Tests: 51; failures: 0; errors: 0.

Strict replacement breaks case_01 and case_07; extended replacement also breaks case_30. Both replacements fail the acceptance gate and remain disabled. Neither supplemental trial recovers a step. The media correction is retained because it fixes cross-row ownership contamination without sample regressions. The status-consistent primary-account slot reached 100% status and 65.6% exact rows on samples but is disabled in the final run, which keeps the baseline that scored higher on the hidden set.

See ownership_trace.md for the complete candidate/lock/elimination trace, evidence_gaps.md for every remaining missing step, and media_audit.md for all 15 media inventories.

Reproduce: `python code/evaluation/main.py`; `python code/evaluation/main.py --cross-case-elimination`; `python code/evaluation/main.py --cross-case-elimination --extended-window`. No command writes log.txt.

## Groq intent comparison

Only the evaluator reads public expected labels. Inference receives request text, the system prompt and policy mode; it never receives expected labels.
Groq openai/gpt-oss-120b uses temperature 0, low reasoning effort and JSON object mode. An explicit refusal always overrides the model; unavailable or invalid answers fall back to rules. Mode shadow keeps rules authoritative while retaining model disagreement diagnostics.

| Metric | Pre-Groq baseline | Final |
|---|---:|---:|
| status_accuracy | 100.0000% | 96.8750% |
| exact_row_accuracy | 65.6250% | 46.8750% |
| sequence_accuracy | 65.6250% | 46.8750% |
| step_precision | 100.0000% | 100.0000% |
| step_recall | 93.7824% | 88.6010% |
| step_f1 | 96.7914% | 93.9560% |
| field_accuracy | 92.2280% | 86.0844% |

Full output NOT_APPLICABLE count: 10 → 10.
Changed NOT_APPLICABLE cases: 0. Degraded metrics: ['status_accuracy', 'exact_row_accuracy', 'sequence_accuracy', 'step_recall', 'step_f1', 'field_accuracy']. Previously correct sample regressions: ['case_02', 'case_08', 'case_10', 'case_22', 'case_31', 'case_32'].

| Changed case | Before NOT_APPLICABLE | After NOT_APPLICABLE | Exact request text |
|---|---|---|---|
| None | — | — | No decisions changed |

Sample agreement between model and rules: N/A: no valid Groq answers; valid model answers 0/32; disagreements 0; unavailable 32.
Sample inference usage (including other requests needed by global ownership): live HTTP calls 0, disk cache hits 0, input tokens 0, output tokens 0.
Full-run agreement: {"agreed": 0, "agreement_rate": null, "cases": 518, "classified": 0, "disagreements": 0, "unavailable": 518}.
Final full-run HTTP failure statuses: {}. Error bodies and credentials are never included.
Chosen default policy: shadow. All classified disagreements are retained as case diagnostics; explicit refusals remain false.

| Sample case | Rules delete | LLM delete | Selected delete | Refusal override | Short reason |
|---|---|---|---|---|---|

**Live-model validation remains pending.** No valid live or cached model answers were available, so the effective decisions came from rules. Agreement cannot be inferred from zero answers. Unit-test response tokens are never included in inference reports. No claim of measured non-zero usage or successful live LLM acceptance is made.

Provider migration: the originally requested llama-3.3-70b-versatile was absent from the authenticated Groq model list and returned HTTP 404 model_not_found. The user explicitly authorized Groq openai/gpt-oss-120b as its replacement; the active model is openai/gpt-oss-120b. Credentials remain environment-only.

Pricing: Groq published on-demand rates checked 2026-10-25; https://console.groq.com/docs/model/openai/gpt-oss-120b . Recheck https://groq.com/pricing before use. Estimates exclude account discounts and provider-side prompt-cache reductions.

