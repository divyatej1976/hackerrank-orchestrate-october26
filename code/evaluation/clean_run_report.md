# Clean extracted-submission run

Date: 25 October 2026. PASS on the Windows host. This is an isolated application/cache test, not a fresh OS or a fresh dependency environment.

## Isolation and setup

- Extracted code.zip into a newly created folder: `.runtime/submission_clean_hu4slh5f`.
- Copied dataset/ beside code/ as ordinary files; did not copy the source workspace runtime/cache directory.
- Asserted `.runtime/` did not exist before the first command.
- Removed GROQ_API_KEY and PYTHONPATH from the child environment. No credential value was printed or written.
- Python 3.12.14; installed pypdf 6.10.0; Pillow 12.3.0.
- Used Windows PowerShell and local Windows.Media.Ocr with the installed OCR language. Ran in the approved normal local environment rather than the restricted agent sandbox.

## Commands and results

| Command, from extracted working folder | Exit code | Result |
|---|---:|---|
| python code/main.py | 0 | 518 predictions generated and internally validated |
| python code/main.py validate | 0 | Output contract validated |

Audit duration: 48.594 s; combined audit and validation: 50.639 s.
Evidence ingestion: 94 files; failures: 0.
Cold screenshot extraction: 22 OCR calls (11 text + 11 layout); zero OCR cache hits.
Groq: zero live calls, zero cache hits, zero input/output tokens. Missing credentials correctly left the default rules-authoritative decision path active.
Output: 518 rows, unique case IDs, sorted by case_id; statuses {"COMPLETE": 153, "INCOMPLETE": 355, "NOT_APPLICABLE": 10}.
Output SHA-256: `cdd74a731f6aacaa678ef50c1ba892257e68d26630f80fd0d0884e45d51d0330`.
The clean output is byte-identical to the current repository output and has zero semantically changed rows. This is a reproduction result, not a new hidden-label accuracy estimate.

## Setup and package changes

README documents the extracted folder layout, python -m pip dependency installation, Windows PowerShell/WinRT OCR and OCR-language prerequisites, and the separate tesseract system dependency on Linux/macOS. No missing Python dependency was found in this run. Linux/macOS were not tested.
The two retained architecture documents describe implemented behavior only. Eleven specified design/planning documents remain in the repository but are excluded from the archive. README contains no references to those excluded filenames.
The original live-model usage report is preserved in the source workspace. The isolated no-key run wrote its zero-token usage report only in the extracted test copy.
After the test, the final archive was rebuilt to include this report and the finalized documentation; no runtime implementation changed.
