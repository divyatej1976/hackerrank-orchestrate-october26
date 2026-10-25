# Ghost Data Still Exists — Research and Product Design

This branch collects the research and design work for the HackerRank Orchestrate deletion-audit agent. The documents are kept separate by purpose.

| Document | Purpose |
|---|---|
| [Market and Problem Research](../code/MARKET_AND_PROBLEM_RESEARCH.md) | Primary-source market review, failure mechanisms, problem priorities, and hypotheses |
| [Product Vision](../code/PRODUCT_VISION.md) | Intended users, product promise, principles, boundaries, and possible evolution |
| [Product Requirements](../code/PRD.md) | MVP scope, exact output contract, user stories, acceptance criteria, and release gates |
| [User Experience](../code/USER_EXPERIENCE.md) | Reviewer journey, case reports, uncertainty handling, and possible future workspace |
| [System Architecture](../code/SYSTEM_ARCHITECTURE.md) | Evidence ingestion, identity resolution, temporal reconstruction, policy checks, and validated export |
| [AI Architecture](../code/AI_ARCHITECTURE.md) | Model boundaries, grounded retrieval, controls and selection criteria |
| [Agent Design](../code/AGENT_DESIGN.md) | Investigator state machine, tools, investigation loop and finalization rules |
| [Prompt Engineering](../code/PROMPT_ENGINEERING.md) | Versioned task prompts, structured outputs, grounding and prompt evaluation |
| [Memory Design](../code/MEMORY_DESIGN.md) | Working state, evidence memory, cache isolation, lifecycle and checkpoints |
| [Database Design](../code/DATABASE_DESIGN.md) | Logical tables, provenance relationships, temporal queries and integrity |
| [API Design](../code/API_DESIGN.md) | Required CLI/internal interfaces and optional future HTTP endpoints |
| [Frontend Design](../code/FRONTEND_DESIGN.md) | Screens, interactions, components, display states and reviewer workspace boundaries |
| [Backend Design](../code/BACKEND_DESIGN.md) | Service ownership, run lifecycle, scheduling, failure recovery and presentation contracts |
| [Development conversation log](../log.txt) | Conversation and development summaries in the repository's logging format |

Read the research and vision first, then the requirements, UX, and architecture. The challenge contract remains in [problem_statement.md](../problem_statement.md).

## Current state

Research and design are prepared. An initial local audit engine, static case report, SQLite observation index, full-dataset CSV, regression tests, and measured evaluation reports are now available. See [implementation instructions](../code/README.md) and [evaluation results](../code/evaluation/evaluation_report.md). Sample exact-match accuracy remains low, so this version is not submission-ready. The broader LLM-assisted architecture, hosted API and interactive workspace remain proposed designs.

The research branch inherits the challenge starter files. This update adds documentation and the conversation log; it does not add a second copy of the evidence corpus or development scratch scripts.
