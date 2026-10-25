# Implemented prompt engineering

Date: 25 October 2026. The implementation has one model prompt: request intent.
Evidence extraction, state reconstruction, policy treatment and ordered steps
are performed by deterministic code, not prompted model tasks.

## Actual prompt and response contract

`prompts/intent_classification.md` is the system message loaded by
`audit/llm.py`. The user message contains only the supplied request text, in its
original language. Workflow claims, evidence artifacts and sample expected
answers are not supplied to the model.

The task is to identify authorization to close/erase an account or delete
personal data, including completion or verification of a previous deletion.
Access/export, correction, login help, marketing-only opt-out and explicit
refusal are non-deletion. The system message instructs the model to treat the
request as untrusted data and ignore embedded instructions that change the task.
It asks for a short reason without personal identifiers or private reasoning.

The only accepted result is a JSON object of this form:

```json
{"deletes": true, "reason": "Account closure requested"}
```

Code requires a real boolean and a nonempty string reason. String booleans,
malformed JSON, missing fields and unusable responses return no model answer.
The reason is bounded to 240 characters. Only the parsed answer and usage are
cached; raw provider responses, headers and reasoning text are not persisted.

## Authority and failure behavior

The shipped `audit/intent_policy.json` selects **shadow**. `rules_intent` makes
the decision; the model supplies a second opinion. Explicit phrases such as
"do not delete", "don't delete" and "not a request to erase" remain false even
in a primary-mode experiment. Refusal normalization handles case, whitespace
and curly apostrophes. Model/rules disagreements retain the case ID, both
answers, the chosen answer and the short model reason in diagnostics.

`--intent-mode primary` uses a valid model answer unless an explicit refusal
wins. `--intent-mode rules` makes no model calls. If GROQ_API_KEY is absent,
HTTP fails or the answer is invalid, the client returns None and code uses the
rules. No key or response is synthesized to make usage appear nonzero.

The primary GPT-OSS trial incorrectly classified four public follow-up requests
as non-deletion. Evaluation therefore retained rules as authoritative. The
current public model/rules agreement is 28/32; exact request texts and rejected
trial metrics are in the evaluation reports. These are evaluation diagnostics,
not case-specific instructions or inference examples.

## Provider configuration

| Setting | Implemented value |
|---|---|
| Provider | Groq |
| Model | `openai/gpt-oss-120b` |
| Endpoint | `https://api.groq.com/openai/v1/chat/completions` |
| Messages | System prompt plus original request text |
| Temperature | 0 |
| Output mode | JSON object |
| Reasoning effort | low |
| Completion limit | 512 tokens |
| Reasoning text | excluded from response |
| HTTP timeout | 20 seconds |
| Retry | Once on 429/5xx |
| Processing | Sequential, with requested inputs primed in their supplied order |

The named application user agent avoids the provider's rejection of urllib's
default user agent. HTTP 401/403/404 opens a per-client access/model failure
circuit; later uncached texts use rules, and a new run retries access.

The user authorized this model after the originally requested Llama model was
unavailable to the account. The application uses the Groq key from the process
environment only. It does not load a dotenv file or use an OpenAI API key.

## Caching and usage

A response cache filename is the SHA-256 of the model name, full system prompt
and exact request text, serialized in stable order. Changing the model or prompt
changes the cache identity. The cache under `.runtime/llm_cache/` contains only
the model name, validated answer and input/output token counts. In-memory
intent memoization prevents repeated global-ownership lookups from counting the
same response again.

Live usage comes from the provider envelope, including known tokens consumed
by an answer later rejected as invalid. Local cache token counts are reported
separately and do not create a new API charge. Failed responses without usage
have unknown consumption; mock-test tokens are not included in run reports.
Call counts include HTTP attempts and retries. Provider status counts and
unavailable-answer coverage are explicit in diagnostics.

`usage_report.md` reports live/cache input/output totals, averages per output
request and estimated incremental API cost. Price constants are centralized in
`audit/llm.py` with the provider documentation reference and a recheck note.
Estimates exclude account discounts and provider-side prompt-cache reductions.
A rejected primary validation run is reported separately from final-run totals.

## Implemented evaluation workflow

`evaluation/main.py` runs inference before reading public expected outputs.
It compares all scored metrics and NOT_APPLICABLE decisions against an
evaluation-only reference. A regressing primary trial switches the global
policy to shadow, regenerates and validates predictions, and reruns sample
inference. The model never receives those expected labels.

The regression suite mocks HTTP and blocks network access in tests. It covers
Spanish account closure, refusal precedence, missing credentials, malformed
JSON, disk/memory cache accounting, prompt invalidation, retries, provider-model
failure and disagreement/coverage accounting. The package includes this actual
prompt and the evaluation/usage reports; it excludes caches and credentials.
