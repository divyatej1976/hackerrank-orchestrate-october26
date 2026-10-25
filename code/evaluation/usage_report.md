# Final-run usage report

Output: `output.csv`; requests: 518; SHA-256: `cdd74a731f6aacaa678ef50c1ba892257e68d26630f80fd0d0884e45d51d0330`.
Elapsed: 129.063 s. Intent mode: shadow; valid request-level agreement: 100.0000%.

| Provider / model / source | Live HTTP attempts | Disk cache hits | Input tokens | Output tokens | Total tokens | Estimated incremental API cost |
|---|---:|---:|---:|---:|---:|---:|
| Groq / openai/gpt-oss-120b / live | 171 | 0 | 18989 | 1929 | 20918 | $0.00400575 |
| Groq / openai/gpt-oss-120b / local response cache | 0 | 311 | 131201 | 13861 | 145062 | $0.00000000 |
| Per-model total: Groq / openai/gpt-oss-120b | 171 | 311 | 150190 | 15790 | 165980 | $0.00400575 |
| Overall token-billed total | 171 | 311 | 150190 | 15790 | 165980 | $0.00400575 |

Average tokens per output request: 320.4247; live 40.3822; cached 280.0425.
Estimated incremental cost per request: $0.0000077331. Estimated uncached-equivalent total cost (including reused responses): $0.03200250.
Price assumptions (USD / 1M tokens): input 0.15; output 0.6. Groq published on-demand rates checked 2026-10-25; https://console.groq.com/docs/model/openai/gpt-oss-120b . Recheck https://groq.com/pricing before use. Estimates exclude account discounts and provider-side prompt-cache reductions.

Failed classifications: 42; distinct texts unavailable because no environment key: 0.
HTTP failures by status (no error bodies retained): {"429": 126}.
Classifications skipped after a terminal provider access/model rejection: 0 (rules fallback; a new client/run retries).
Live calls count HTTP attempts, including retries. Tokens on a successful API envelope count even if answer JSON is rejected. Failed requests without returned usage have unknown tokens, not estimated tokens. Local cache tokens are counted separately and incur no new API charge. Repeated in-process lookups reuse memory without counting the same response again.
The global ownership solver can classify other supplied requests as context; their usage is included. Requests are processed sequentially, with no concurrent API calls. Cache identity includes the model, full prompt and exact request text.
Local OCR: 0 calls; 22 cache hits. Windows.Media.Ocr model identifier is OS-managed and unavailable; tokens N/A; API cost $0. Local compute and development-chat costs are not measured.

## Rejected primary validation run (separate from final-run totals)

Provider/model: Groq / openai/gpt-oss-120b; live HTTP calls 770; live input tokens 90704; live output tokens 9458; cache hits 0; cached input tokens 0; cached output tokens 0. Estimated incremental cost $0.01928040. These development-validation calls are not counted again as live calls when their cached responses are reused by the final shadow run.
