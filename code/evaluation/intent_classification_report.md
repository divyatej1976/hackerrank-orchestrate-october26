# Groq intent classification evaluation

Only the evaluator reads public expected labels. Inference receives request text, the system prompt and policy mode; it never receives expected labels.
Groq openai/gpt-oss-120b uses temperature 0, low reasoning effort and JSON object mode. An explicit refusal always overrides the model; unavailable or invalid answers fall back to rules. Mode shadow keeps rules authoritative while retaining model disagreement diagnostics.

| Metric | Pre-Groq baseline | Final |
|---|---:|---:|
| status_accuracy | 100.0000% | 100.0000% |
| exact_row_accuracy | 65.6250% | 65.6250% |
| sequence_accuracy | 65.6250% | 65.6250% |
| step_precision | 100.0000% | 100.0000% |
| step_recall | 93.7824% | 93.7824% |
| step_f1 | 96.7914% | 96.7914% |
| field_accuracy | 92.2280% | 92.2280% |

Full output NOT_APPLICABLE count: 10 → 10.
Changed NOT_APPLICABLE cases: 0. Degraded metrics: []. Previously correct sample regressions: [].

| Changed case | Before NOT_APPLICABLE | After NOT_APPLICABLE | Exact request text |
|---|---|---|---|
| None | — | — | No decisions changed |

Sample agreement between model and rules: 87.5000%; valid model answers 32/32; disagreements 4; unavailable 0.
Sample inference usage (including other requests needed by global ownership): live HTTP calls 79, disk cache hits 356, input tokens 159915, output tokens 16891.
Full-run agreement: {"agreed": 457, "agreement_rate": 1.0, "cases": 518, "classified": 457, "disagreements": 0, "unavailable": 61}.
Final full-run HTTP failure statuses: {"429": 126}. Error bodies and credentials are never included.
Chosen default policy: shadow. All classified disagreements are retained as case diagnostics; explicit refusals remain false.

| Sample case | Rules delete | LLM delete | Selected delete | Refusal override | Short reason |
|---|---|---|---|---|---|
| case_06 | True | False | True | False | User requests removal of a search result, not account deletion or data erasure. |
| case_21 | True | False | True | False | User is asking for verification of a prior deletion, not requesting a new deletion. |
| case_25 | True | False | True | False | User is asking for status of a prior deletion request, not authorizing a new deletion |
| case_27 | True | False | True | False | User is asking for audit/confirmation of a past deletion, not requesting a new deletion. |

## Rejected primary trial

Rules were retained as the decision and the LLM downgraded to a second opinion because a metric/case regressed or the NOT_APPLICABLE set changed. Every changed decision is conservatively flagged for text review; no label is passed into inference.
Degraded metrics: ['status_accuracy', 'exact_row_accuracy', 'sequence_accuracy', 'step_recall', 'step_f1', 'field_accuracy']. Regressed cases: ['case_06'].

| Trial changed case | Request text |
|---|---|

Provider migration: the originally requested llama-3.3-70b-versatile was absent from the authenticated Groq model list and returned HTTP 404 model_not_found. The user explicitly authorized Groq openai/gpt-oss-120b as its replacement; the active model is openai/gpt-oss-120b. Credentials remain environment-only.

Pricing: Groq published on-demand rates checked 2026-10-25; https://console.groq.com/docs/model/openai/gpt-oss-120b . Recheck https://groq.com/pricing before use. Estimates exclude account discounts and provider-side prompt-cache reductions.


## Rejected primary trial: public NOT_APPLICABLE changes

The pre-Groq sample status accuracy was 100%, so these expected statuses also describe the correct baseline decisions. The final shadow policy restores them; the full 518-row NOT_APPLICABLE set is unchanged.

| Public case | Correct baseline status | Rejected primary status | Exact request text |
|---|---|---|---|
| case_06 | INCOMPLETE | NOT_APPLICABLE | My account page is gone, but my old profile still appears when I search for it. Can you remove that search result too? |
| case_21 | COMPLETE | NOT_APPLICABLE | I deleted my account and received the confirmation email. Could you verify that the profile is gone and that anything retained for security is limited to what is required? |
| case_25 | COMPLETE | NOT_APPLICABLE | The privacy page still says my request failed. Please inspect the actual systems and tell me whether the account and identifiable analytics data have already been removed. |
| case_27 | COMPLETE | NOT_APPLICABLE | Please audit the deletion as it stood when my request was reviewed. I want confirmation that the account was fully removed at that point. |

