# Frontend Design

Date: 24 October 2026 · Status: design only

## 1. Purpose and scope

Design a reviewer workspace for inspecting deletion audits and handing off remediation plans. This is an optional presentation layer over the audit engine. The required challenge interface remains the CLI and exact CSV export. No application, component, or stylesheet is implemented by this document.

The workspace should answer: what is the audit decision, what evidence supports it, what remains or can return, what must be retained, and what checks are still required?

## 2. Navigation and screens

| Screen | Contents | Primary action |
|---|---|---|
| Audit runs | Run identifier, dataset version, time, processing state, case counts and validation state | Open run |
| Start audit | Registered dataset, request set, pinned configuration and destination summary | Start audit |
| Run overview | Stage progress, verdict counts, unresolved work, ingestion failures and export readiness | Review cases |
| Case queue | Case ID, audit time, workflow claim, audit verdict, processing state and issue count | Inspect case |
| Case detail | Decision, findings, retention obligations, remediation, verification, identity and timeline | Inspect supporting evidence |
| Evidence panel | Source region, locator, times, store scope and supporting observation | Navigate related finding |
| Export summary | Run version, schema/citation checks, row count and artifact identity | Download validated CSV |

The first web version uses registered datasets. General file upload, live database credentials, remediation execution and manual verdict overrides are separate future requirements.

## 3. Case-detail wireframe

```text
Runs / Selected run / Case reference

Audit verdict: INCOMPLETE          Processing: Validated
Audit time: explicit UTC timestamp   Workflow claim: COMPLETE
Reason: one retained message exposes identifiers; one relevant flow is enabled

[Findings] [Plan] [Retention] [Coverage] [Identity] [Timeline]

Selected tab content                         Evidence panel
----------------------------------           ----------------------------
System / resource / observed state            Source ID and locator
Required policy treatment                    Captured and observed times
Evidence link                                Store or replica scope
                                             Relevant source excerpt
```

Illustrative content is not a dataset prediction. The evidence panel opens from a finding, obligation or timeline observation and preserves the selected case/tab. On smaller screens it becomes a full-width panel with an explicit return action.

## 4. Interaction rules

The case queue supports server-side search by case/resource reference and filters for verdict, processing state, affected system and risk type. Preserve filters in the URL. Keep workflow claims visually separate from audit decisions.

Findings identify resource, violation, required treatment and source. Clicking evidence opens the exact source region, not an unbounded raw document by default. Identity history shows grounded links and their provenance; uncertain links are labeled and do not appear as confirmed merges.

The plan has separate findings, remediation and verification sections in challenge order. Incomplete-case checks say “Required after remediation.” A proposed action is never displayed as executed. Retention is a dedicated view and is also visible beside affected resources.

For `NOT_APPLICABLE`, show the interpreted request scope and explain why no deletion steps were produced. Detailed subject investigation is unnecessary once non-deletion is established.

## 5. Visual language

Use a restrained, evidence-oriented interface: neutral surfaces, readable typography, compact tables with adequate spacing, and consistent source links. Avoid decorative charts that obscure the resource-level facts.

| Meaning | Label and visual treatment |
|---|---|
| Proven compliant audit | COMPLETE with a check icon and green accent |
| Supported violation | INCOMPLETE with warning icon and amber accent |
| No deletion authorization | NOT APPLICABLE with neutral icon and gray accent |
| Material proof gap | Review needed with question icon and distinct accent |
| Processing failure | Failed with error icon and red accent |

Color never carries meaning alone. A coverage graphic, if used, distinguishes satisfied, violated and unresolved obligations. Its denominator is known obligations, not all possible systems or a probability that deletion succeeded. Show counts alongside any graphic.

## 6. Component model

Proposed reusable components: application shell, run selector, stage progress, case table, verdict badge, processing-state badge, finding row, obligation table, ordered plan, evidence drawer, identity history, observation timeline, issue list and export validation summary.

The frontend owns selection, navigation, filters, disclosure state and display preferences. The backend owns eligibility, policy, counts, verdicts, plan ordering and export readiness. The browser must not recompute a verdict or enable export based only on locally cached counts.

Frontend framework and component-library selection remain open. The design can be implemented using a typed component-based web stack; choosing versions or dependencies belongs to implementation planning.

## 7. State and data loading

Key cached responses by caller scope, run ID, case ID and snapshot/result version. Discard sensitive cached data on sign-out or scope change. Do not store evidence or full identifiers in browser local storage.

Fetch run summaries and case pages independently. Poll active runs at a bounded interval, back off after failures, and stop on terminal states. Display the last update time and stale state when refresh fails. A case may be reviewable before a run finishes, but partial results are labeled provisional until validated.

Use explicit loading, empty, unavailable, review-needed, failed and validated states. “No findings” cannot substitute for “Audit complete.” A stale request response must not replace the newly selected case's data.

## 8. Accessibility and information protection

All controls support keyboard navigation, visible focus, semantic headings and descriptive labels. Tables preserve header associations. The evidence panel moves focus on open and returns it to its trigger on close. Timeline and graph information must also be available as a textual list. Do not rely on hover for essential facts.

Mask identifiers in summaries where feasible; authorized detail views can reveal what the reviewer needs. Render document text as text, not executable markup. Avoid leaking identifiers into URLs, telemetry, browser logs or error messages. Server authorization remains required even when an action is hidden in the UI.

## 9. Frontend acceptance scenarios

- Reviewer locates a violation and opens the source region supporting it.
- A primary absence and replica presence remain distinguishable.
- Future checks cannot be mistaken for completed checks.
- Required retention is visible without reading every remediation row.
- Unresolved cases prevent a misleading ready-to-export state.
- API failure shows an error rather than clearing the findings into an apparent successful result.
- A stale response cannot show another case's evidence under the current case heading.
- An export identifies the exact validated run and contains the prescribed CSV schema.

These are planned usability and integration checks, not completed test results.

## Related designs

[User Experience](USER_EXPERIENCE.md), [Backend Design](BACKEND_DESIGN.md), [API Design](API_DESIGN.md), and [PRD](PRD.md).
