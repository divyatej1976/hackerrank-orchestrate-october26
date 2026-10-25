# Memory Design

Date: 24 October 2026 · Status: proposed design

## Decision

Use explicit structured memory with provenance, time, and lifecycle. Conversation history is not the source of truth for audit decisions. Do not introduce an unrestricted long-term agent memory or learned case-label store.

| Memory type | Contents | Lifetime | Authority |
|---|---|---|---|
| Case working state | Eligible subject links, retrieved references, unresolved questions, visited queries | Case/run; checkpointed for resume | Derived, must reference observations |
| Evidence memory | Parsed observations, source locations, scope and timestamps | Dataset version; disposable/rebuildable | Grounded observations, not infallible truth |
| Identity memory | Typed identity edges with validity and availability times | Dataset version | Requires provenance and cutoff filtering |
| Policy memory | Supplied rules, parsed conditions, policy hash | Policy version | Authoritative only for that run's supplied policy |
| Extraction cache | Validated candidates, extractor/prompt/model versions, source hash | Until source/config version changes or explicit purge | Reusable interpretation, still needs case eligibility checks |
| Run memory | Progress, retries, usage, errors, output hash and validation state | Reproducibility window configured by operator | Operational record |
| Development transcript | User prompts and agent summaries required by AGENTS.md | Challenge lifecycle under user control | Development provenance; never inference evidence |

## Retrieval and isolation

Each context build starts with a case ID, dataset version and audit cutoff. Retrieve exact identity/resource matches first, then follow grounded edges. A context allowlist records which source fragments were provided. Validate outputs against that allowlist.

Global evidence may be shared, but case-derived conclusions are namespaced by case/run. Do not reuse another case's verdict as evidence. A cache may hold future observations globally; case retrieval must still reject facts unavailable at its cutoff.

## Cache key

Proposed key: hash of source bytes, source region, task/schema version, extractor version, prompt version, model/configuration, and any task-specific context that affects interpretation. Case-conditioned tasks also include the relevant cutoff, policy version and input references. Never key solely by filename or case ID.

Store failure state separately from successful empty extraction. A parser bug fix or policy change invalidates affected derived results. Changed policy need not invalidate literal source extraction, but must invalidate assessments and plans.

## Checkpoints and bounded context

Persist the investigation frontier, observation references, obligation states, query history and budget counters after each completed stage. Resume only when input/configuration hashes match. Recompute derived conclusions when they do not.

Use evidence references and structured facts to keep context small. Summaries are navigation aids, not substitutes for source facts. If context is truncated, record omitted items and do not imply full coverage.

## Privacy and lifecycle

Raw evidence remains in the dataset; avoid duplicate full documents and PII in prompts/logs where a bounded excerpt suffices. Exact matching can use normalized values in a restricted local store, or keyed lookup digests with collision handling when production requirements justify them. Digests remain linkable identifiers; hashing is not automatically anonymization.

No runtime retention duration is invented here. Make retention/purge configuration explicit, excluding any supplied records policy requires to remain available. Purging derived memory must include indexes, caches, temporary media and exported reports where applicable; preserve source corpus and required transcript according to the applicable workflow. The challenge audit does not itself delete these files.

## Memory correctness tests

- Changing source bytes invalidates extraction reuse.
- An earlier audit cannot retrieve later cached evidence.
- One subject's facts do not leak into another case's context.
- Failed extraction is never recalled as proven absence.
- Policy changes recompute obligations without altering original observations.
- Resume with changed inputs is rejected or explicitly restarted.
- Summary loss cannot erase a source-backed retention obligation.
