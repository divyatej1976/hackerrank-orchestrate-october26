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

Tests: 36; failures: 0; errors: 0. Test fixtures are participant-authored and do not read expected answers.

| Authored input | Required result | Outcome |
|---|---|---|
| Export request explicitly prohibits deletion | NOT_APPLICABLE, empty steps | PASS |
| Search record exists and sync is active | Disable writer before deleting dependent record | PASS |
| Redacted tombstone, retained audit record, blocked backup | COMPLETE with all three policy checks | PASS |
| State correction arrives after audit cutoff | Earlier noncompliant state remains decisive | PASS |
| Unknown email on neighboring visual table row | Does not inherit sole recognized page customer | PASS |
| Worker event after report but before audit | Extended ownership only when forced; two candidates abstain | PASS |
| Explicit lookup lock and competing requests | Lock provenance retained and candidate elimination traced | PASS |

Other regressions cover null/404 lookup ownership, historical aliases, replica drift, incomplete-case full verification, future ownership versus eligible state, contested singletons, input-order determinism and conflicting primary account locks.

## Changes and remaining failures

- Added auditable direct-lock provenance, deterministic propagation traces and fixed-point candidate lists over both request files.
- Tested the full audit-time episode window separately. Strict replacement and wider replacement fail the no-regression gate; both remain disabled. Supplemental variants preserve existing results but add no steps.
- Fixed media ownership contamination from unknown neighboring emails and classified state from local resource context.
- Inventoried all 11 screenshots and 4 PDFs, including recognized identifiers, OCR variants, short checksums, statuses, observations and remaining OCR omissions.
- Ownership cannot be resolved by operation SUCCESS/FAILED, case/resource ID patterns, row order, timestamp proximity, or expected answers.

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
| Final: media fix; elimination disabled | 96.8750% | 46.8750% | 46.8750% | 100.0000% | 88.6010% | 93.9560% | 86.0844% |

Final previously-correct sample regressions: []. All 15 original exact-correct cases checked. Final matching steps: 171/193; missing: 22; extra: 0.
Tests: 36; failures: 0; errors: 0.

Strict replacement breaks case_01 and case_07; extended replacement also breaks case_30. Both replacements fail the acceptance gate and remain disabled. Neither supplemental trial recovers a step. The media correction is retained because it fixes cross-row ownership contamination without sample regressions. Exact-row accuracy did not increase; preserving precision and abstaining on unresolved ownership takes precedence over guessing.

See ownership_trace.md for the complete candidate/lock/elimination trace, evidence_gaps.md for every remaining missing step, and media_audit.md for all 15 media inventories.

Reproduce: `python code/evaluation/main.py`; `python code/evaluation/main.py --cross-case-elimination`; `python code/evaluation/main.py --cross-case-elimination --extended-window`. No command writes log.txt.

## Limits

Exact-row accuracy is 46.8750%. Missing expected steps: 22; extra: 0. Unresolved sample decisions: 1. See evidence_gaps.md for all candidates and grouped reasons.
The media recheck uses existing OCR caches, not a new OCR model. Three small security reference IDs remain unread by OCR, as documented in media_audit.md. Identity availability and multilingual intent handling remain limited. The current agent uses deterministic extraction and local OCR, with no remote generative model. A contract-valid full-dataset output does not prove semantic accuracy.

## Reproduction

Run `python code/evaluation/main.py`. Use --cross-case-elimination, optionally --extended-window and --supplemental, to reproduce the rejected/supplemental trials. Run `python code/main.py`, then `python code/main.py validate` for final predictions. No workflow writes log.txt.
