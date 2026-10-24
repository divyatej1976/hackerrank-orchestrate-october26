# Ghost Data Still Exists — Product Vision

Version: 1.0 · Date: 24 October 2026 · Status: proposed product direction

## Vision

Give privacy teams and engineers a defensible answer to a difficult question: **has this person's data received every treatment required by policy, and can prohibited data come back?**

The product turns scattered evidence into a traceable deletion decision and an actionable path to completion. Every conclusion states what the evidence establishes at the audit time. Required retained records remain available.

## Who we serve

Our primary user is a privacy operations reviewer validating a completed or disputed deletion request. Their immediate need is to understand what remains, why it matters, and what evidence supports the decision.

The second user is the data or platform engineer responsible for remediation. They need exact resources, the required treatment, recreation controls to apply first, and final-state checks.

A compliance reviewer needs assurance that the plan preserves required records and removes only prohibited identifiers. These roles are product assumptions based on the challenge; customer interviews have not yet validated buying behavior.

## Product promise

For each authorized deletion request, provide:

1. A decision grounded in the supplied evidence at the audit cutoff.
2. A connected view of current and historical identifiers and relevant resources.
3. Findings covering residual records, exposed identifiers, and recreation risks.
4. Ordered, policy-safe remediation and verification steps.
5. Traceability from each finding or current-state check to supporting evidence.

For a request that does not authorize deletion, return `NOT_APPLICABLE` with no deletion steps.

## Desired user experience

A reviewer supplies a request and the available evidence. The agent establishes authorization, follows identity links, inspects relevant copies, checks policy obligations, and reconstructs state at the requested time. The reviewer receives a clear decision and can inspect the evidence behind each finding. An engineer can use the resulting plan without guessing which resources or treatments are intended.

In the challenge MVP, this experience is delivered through a terminal workflow and the exact required CSV. A visual review interface is a possible later extension.

## Principles

- **Evidence before completion:** an operation-success message is insufficient proof of resulting state.
- **Respect authorization:** access, correction, export, and marketing-only requests do not imply account deletion.
- **Follow identity history:** relevant copies may use an old identifier or a stable internal reference.
- **Treat scope explicitly:** absence in one store does not prove absence in its replicas or archives.
- **Make deletion durable:** investigate active writers and restore paths as well as stored records.
- **Preserve required data:** correct retention is part of successful deletion.
- **Make uncertainty visible:** parsing gaps and conflicting evidence must not become silent completion claims.
- **Use AI with checks:** interpretation can use AI; policy application, timestamps, citations, and output structure require validation.

## Definition of success

Success means a reviewer can distinguish proven completion from unresolved or demonstrated failure, and an engineer can carry out the policy-safe plan with clear verification obligations.

For the MVP, measure status and step correctness, false-complete decisions, unauthorized plans, retention violations, citation validity, and processing coverage. Runtime and model cost matter after correctness. Specific metrics and release gates live in the PRD.

## Product boundaries

The first version audits supplied files and proposes remediation. It does not execute destructive actions, replace the supplied policy, or guarantee absence in systems outside the evidence universe. A complete verdict concerns the specified audit time; it cannot guarantee that future configuration changes will never recreate data.

## Product evolution

| Horizon | Outcome | Condition for proceeding |
|---|---|---|
| 1. Challenge MVP | Reproducible evidence audit, exact predictions, evaluation and usage reports | Required functional and submission gates pass |
| 2. Reviewer workspace | Inspect identity links, timelines, coverage gaps and evidence | Users demonstrate a need beyond the CSV workflow |
| 3. Connected assurance | Read-only checks against supported live systems | Connector scope, permissions and evidence semantics validated |
| 4. Continuous assurance | Detect meaningful regressions after deletion | Live checks are reliable and operational ownership is established |

These are possible horizons, not committed delivery dates. Production execution requires a separate requirements and authorization design.

## Positioning hypothesis

An evidence-backed deletion assurance agent for teams that need to validate completion across distributed systems and mixed artifacts. The proposed emphasis is historical reconstruction, recreation risks, and retention-safe proof. Research has not established that these capabilities are unique or that customers will buy a standalone product.

## Document boundaries

- [Product requirements](PRD.md): what the MVP must do and how acceptance is measured.
- [Market and problem research](MARKET_AND_PROBLEM_RESEARCH.md): external evidence, market capabilities, and hypotheses to validate.

This document owns the intended outcome, user promise, principles, and longer-term direction.
