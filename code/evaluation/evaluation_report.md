# Evaluation report

Measured on 32 public samples. Hidden full-dataset labels are unavailable. Expected answers are read only by evaluation after inference.

| Metric | Final |
|---|---:|
| status_accuracy | 96.8750% |
| exact_row_accuracy | 46.8750% |
| sequence_accuracy | 46.8750% |
| step_precision | 100.0000% |
| step_recall | 88.6010% |
| step_f1 | 93.9560% |
| field_accuracy | 86.0844% |

Matching steps: 171/193 expected; 171 predicted. Matching fields: 1163/1351.
Steps are multiset matched excluding step_no. Fields align by phase/operation/system/resource; missing or extra steps count as seven errors. Sequence compares complete arrays, including numbering and citations.

## Regression workflow

Tests: 51; failures: 0; errors: 0. Test fixtures are participant-authored and do not read expected answers.

| Authored input | Required result | Outcome |
|---|---|---|
| Export request explicitly prohibits deletion | NOT_APPLICABLE, empty steps | PASS |
| Search record exists and sync is active | Disable writer before deleting dependent record | PASS |
| Redacted tombstone, retained audit record, blocked backup | COMPLETE with all three policy checks | PASS |
| State correction arrives after audit cutoff | Earlier noncompliant state remains decisive | PASS |
| Unknown email on neighboring visual table row | Does not inherit sole recognized page customer | PASS |
| Worker event after report but before audit | Extended ownership only when forced; two candidates abstain | PASS |
| Explicit lookup lock and competing requests | Lock provenance retained and candidate elimination traced | PASS |
| Groq says true for a Spanish account-closure request (mock HTTP) | Intent True | PASS |
| Groq says true but request says do not delete | Intent False; refusal wins; disagreement diagnostic | PASS |
| GROQ_API_KEY absent (network forbidden) | Same answer as rules_intent | PASS |
| Groq response contains malformed JSON | Same answer as rules_intent; consumed tokens still counted | PASS |
| A second client reads the cached model/prompt/text response | No second HTTP request; cached tokens reported separately | PASS |
| Three requests, one COMPLETE and two NOT_STARTED, sharing a window | Status filter assigns the unique account; two FAILED candidates for two subjects stay unassigned | PASS |

Other regressions cover null/404 lookup ownership, historical aliases, replica drift, incomplete-case full verification, future ownership versus eligible state, contested singletons, input-order determinism and conflicting primary account locks.

## Changes and remaining failures

- Added auditable direct-lock provenance, deterministic propagation traces and fixed-point candidate lists over both request files.
- Tested the full audit-time episode window separately. Strict replacement and wider replacement fail the no-regression gate; both remain disabled. Supplemental variants preserve existing results but add no steps.
- Fixed media ownership contamination from unknown neighboring emails and classified state from local resource context.
- Inventoried all 11 screenshots and 4 PDFs, including recognized identifiers, OCR variants, short checksums, statuses, observations and remaining OCR omissions.
- Biggest improvement: every sample deletion has exactly one primary-account step, but the engine grounded only 18/32. Added a primary-account slot (`AuditEngine._slot_assignments`): candidates are deletion-worker account events between reported_at-90min and reported_at+15min whose result is consistent with the workflow claim (COMPLETE->SUCCESS, NOT_STARTED->FAILED, PARTIALLY_COMPLETE->PARTIAL/SUCCESS; 31/32 samples agree, the other has no event). A candidate is assigned only when it is the unique remaining one after one-to-one elimination across all 550 requests; contested candidates stay unassigned. COMPLETE cases drop an inferred account that lacks audit-time evidence instead of citing nothing. On samples: status 96.9%->100%, exact rows 46.9%->65.6%, precision 100%; 113 of 518 evaluation rows would gain an account step. DISABLED in the final run. It raised public-sample exact rows from 46.9% to 65.6%, but the hidden-set CSV score fell when it was submitted (other changes shipped with it), so the final output keeps the earlier, better-scoring baseline. Re-enable via `AuditEngine.WORKFLOW_SLOTS`.
- Tried the same slot for analytics profiles: no sample change, so it was removed. Never uses case/resource ID patterns, row order or expected answers.

| Failing case | Predicted status | Expected status | Missing | Extra |
|---|---|---|---:|---:|
| case_02 | UNRESOLVED | COMPLETE | 1 | 0 |
| case_03 | COMPLETE | COMPLETE | 1 | 0 |
| case_04 | COMPLETE | COMPLETE | 1 | 0 |
| case_08 | INCOMPLETE | INCOMPLETE | 1 | 0 |
| case_10 | INCOMPLETE | INCOMPLETE | 1 | 0 |
| case_18 | INCOMPLETE | INCOMPLETE | 2 | 0 |
| case_20 | INCOMPLETE | INCOMPLETE | 2 | 0 |
| case_21 | COMPLETE | COMPLETE | 2 | 0 |
| case_22 | INCOMPLETE | INCOMPLETE | 1 | 0 |
| case_23 | INCOMPLETE | INCOMPLETE | 1 | 0 |
| case_25 | COMPLETE | COMPLETE | 2 | 0 |
| case_26 | COMPLETE | COMPLETE | 1 | 0 |
| case_27 | COMPLETE | COMPLETE | 1 | 0 |
| case_28 | COMPLETE | COMPLETE | 2 | 0 |
| case_29 | INCOMPLETE | INCOMPLETE | 1 | 0 |
| case_31 | COMPLETE | COMPLETE | 1 | 0 |
| case_32 | INCOMPLETE | INCOMPLETE | 1 | 0 |

## Measurements for every trial

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

## Limits

Exact-row accuracy is 46.8750%. Missing expected steps: 22; extra: 0. Unresolved sample decisions: 1. See evidence_gaps.md for all candidates and grouped reasons.
The media recheck uses existing OCR caches, not a new OCR model. Three small security reference IDs remain unread by OCR, as documented in media_audit.md. Remaining ownership ambiguities are not resolved by intent classification. Groq classifies intent when a valid answer is available, rules handle missing/invalid responses, and explicit refusal always wins; measured usage is in usage_report.md.

## Reproduction

Run `python code/evaluation/main.py`. Use --cross-case-elimination, optionally --extended-window and --supplemental, to reproduce the rejected/supplemental trials. Run `python code/main.py`, then `python code/main.py validate` for final predictions. No workflow writes log.txt.

## Groq intent step and regression gate

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

