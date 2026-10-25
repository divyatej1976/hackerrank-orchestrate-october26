# Final-run usage report

Output: `output.csv`; 518 requests; SHA-256 `5171c07a268a6d3d8d0f8e904aee66b6ce3bf7ecc49d9c239fca0e40b9b11a4c`.
Elapsed time: 6.416 seconds on this machine with the existing OCR cache.

| Provider / model | Calls in final run | Input tokens | Output tokens | Total tokens | Estimated API cost |
|---|---:|---:|---:|---:|---:|
| Remote LLM: none | 0 | 0 | 0 | 0 | $0.00 |
| Local Windows.Media.Ocr (OS-managed model; internal model identifier not exposed) | 0 | N/A | N/A | N/A | $0.00 |

OCR cache hits: 22. Cold setup used two local OCR passes per screenshot (text and spatial layout) for 11 screenshots; those setup calls are not final-run calls.
No hosted generative model was called by inference. Token total and average per request: 0 and 0. Estimated total and per-request API cost: $0.00 and $0.00.
Local CPU/electricity and development-chat usage are not measured or included in API cost. OCR uses images and text, not a token-billed interface.
This report reflects the actual current implementation, not the proposed LLM-assisted architecture.
