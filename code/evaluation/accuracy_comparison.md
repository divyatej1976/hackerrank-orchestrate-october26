# Accuracy comparison

Public samples only. Expected answers are read exclusively in code/evaluation/. No sample labels or target resource IDs are used by inference.

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
