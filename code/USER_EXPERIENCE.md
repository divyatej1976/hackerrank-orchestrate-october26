# Ghost Data Still Exists — User Experience

Version: 1.0 · Date: 24 October 2026 · Status: proposed design

## 1. Experience goal

Help a reviewer answer: **what remains, what can recreate it, what must be preserved, and what proves completion?**

The experience should reveal the decision first, then let the reviewer inspect identity links, observations, policy obligations, and proposed actions. It must distinguish the observed state from a future state that remediation would establish.

The challenge MVP uses a terminal workflow, the required CSV, and a separate readable audit report. The report is a proposed companion artifact; it does not change the submission schema. A browser workspace is a later interface for the same audit model.

## 2. Primary journey

| Stage | User need | MVP interaction | Outcome |
|---|---|---|---|
| Prepare | Know what will be audited | Supply dataset location; see request count, evidence inventory, policy and output destination | Scope is explicit |
| Run | Know whether investigation is progressing | Stage-level progress: ingestion, identity, reconstruction, planning, validation | Work and failures remain visible |
| Triage | Know which cases need attention | Run summary with verdict counts and separate unresolved-case count | Reviewer chooses cases to inspect |
| Investigate | Understand why the decision was made | Read case report with evidence references and policy reasoning | Finding is defensible |
| Handoff | Know what engineers must do | Ordered remediation and verification plan | Specific work can be assigned |
| Export | Obtain valid submission files | Export after contract validation; show final paths and validation result | Complete CSV and reports are available |

No deletion confirmation dialog is needed for this audit-only MVP. It does not execute remediation.

## 3. Case report information hierarchy

### A. Decision summary

Show the case ID, audit timestamp and timezone, requested action, deletion verdict, and a short explanation. Show workflow-reported status separately so it cannot be confused with the audit decision.

Examples below are illustrative, not dataset predictions:

- **Incomplete:** “A support attachment remains and a relevant connector is enabled. Disable the connector, delete the attachment, and run the listed checks.”
- **Complete:** “The supplied evidence supports the required treatments and recreation controls at the audit time. Required retained records remain available.”
- **Not applicable:** “The message requests an account export and does not authorize deletion. No deletion steps were generated.”

If the audit is unresolved internally, show “Review needed” in the companion report with the missing proof. This is a processing state, never a fourth CSV verdict. The system must not claim that every case has a final answer while material questions remain.

### B. What remains and what can return

List findings with system, resource, observed problem, policy obligation, observation time, and source reference. Distinguish residual records, exposed identifiers in retained records, active flows, and restore risks through clear labels.

### C. What must be preserved

List retained security/legal records, policy-required archives, and permitted stable tombstone references. Explain which identifiers must be removed and which reference may remain. Preservation should be visible alongside removal actions.

### D. What to do next

Show findings, remediation, and verification as separate sections. Remediation begins with disabling relevant flows and blocking unsafe restores, followed by the required record treatments. Label verification for an incomplete case as “Checks required after remediation,” never “Passed.”

Display final steps in the exact challenge operation order. A dependency explanation can accompany the steps but must not reorder the CSV contract.

### E. Evidence and coverage

Allow inspection of source ID, file or row/page location, capture time, observation time, store/replica scope, and the specific fact supporting a decision. Present conflicting observations together with the reason one does or does not supersede another.

Show extracted facts and relevant short source excerpts rather than private model reasoning. Mask direct identifiers in summary views where possible. Distinguish a query identifier from an identifier present in returned data.

## 4. Proposed reviewer workspace

```text
Audit queue
  Case | Audit time | Workflow claim | Audit verdict | Review needed
                              |
                              v
Case detail
  Decision and scope
  Findings | Required retention | Remediation | Verification
  Identity history | Resource coverage | Timeline | Evidence
```

The queue supports filtering by audit verdict, unresolved state, system, and risk type. Search supports case/resource references. A case detail view links each finding to its source observation and policy rule. This is an information architecture proposal, not a commitment to build a UI for the challenge.

## 5. Error and uncertainty behavior

| Situation | Experience |
|---|---|
| Missing required input or invalid policy | Stop with the file/field problem and corrective action |
| Unreadable evidence | Identify the file, extraction stage, and potentially affected scope; retry or review |
| Ambiguous identity | Show competing grounded links; do not silently merge people |
| Contradictory state evidence | Show time and replica scope; explain whether reconciliation is possible |
| Post-cutoff evidence | Exclude from the verdict; optionally list as excluded context |
| Missing required retained record | Identify the policy conflict and operation-contract limitation |
| Material proof gap | Mark internally for review; prevent an unsupported final export |
| Output validation failure | Preserve the previous final output and provide an actionable error |

## 6. UX acceptance criteria

- A reviewer can distinguish the workflow claim, observed audit verdict, and future verification state.
- Each finding exposes its resource, supporting evidence, and required treatment.
- Required retained records are easy to identify.
- Unresolved cases and extraction failures remain visible in the run summary.
- A non-deletion request produces no proposed destructive work.
- Timestamps are explicit; the CSV retains the supplied time semantics.
- All exported steps match the required schema and order.
- The audit report does not claim execution or verification that has not occurred.

## 7. Usability validation plan

Use authored cases to ask a reviewer to identify the verdict, locate its evidence, explain a retention decision, and identify the first remediation action. Record task success, mistakes, and time to a correct explanation. These sessions have not been conducted. Avoid claiming usability improvements before measuring them.

## Related documents

[Product Vision](PRODUCT_VISION.md) defines the intended outcome. [PRD](PRD.md) defines acceptance requirements. [System Architecture](SYSTEM_ARCHITECTURE.md) defines how the system supports this experience.
