# Ghost Data Still Exists — Market and Problem Research

Research date: 24 October 2026. Scope: public primary-source desk research and the supplied challenge contract. No customer interviews or vendor product trials have been conducted.

## 1. Research conclusion

The strongest product hypothesis is an **evidence-backed deletion assurance agent**: investigate a completion claim, reconstruct the state across relevant copies at a specified time, find recreation paths, and produce a policy-safe remediation and verification plan.

Privacy request automation is already an established product category. Discovery, identity enrichment, deletion orchestration, redaction, and audit trails are existing capabilities. The opportunity we should test is whether an independent audit across mixed evidence can reduce false completion decisions and investigation effort. Public documentation does not prove that competitors cannot do this; that requires product testing and customer research.

For the hackathon, implement this as a reproducible offline audit engine over the supplied corpus. Production connectors, continuous monitoring, and execution are later extensions.

## 2. What the problem statement actually asks us to solve

The fictional $2.4 million loss is scenario context, not a verified market statistic. The immediate symptom—an email remaining registered—could result from a residual identifier or a recreated record. The agent must investigate the evidence rather than assume either cause.

The challenge combines six distinct problems:

1. **Authorization:** does the message request deletion, rather than access, correction, export, or marketing opt-out?
2. **Identity continuity:** which historical emails, phones, hashes, and stable references belong to the same person?
3. **Copy discovery:** where do those identifiers occur across stores, replicas, attachments, indexes, and exports?
4. **Temporal reconstruction:** what was true at `audit_at`, rather than at the time of a later fix?
5. **Policy-safe treatment:** which records must be deleted, redacted, anonymized, or retained?
6. **Durability of deletion:** can a connector, import, replication, or restore path recreate prohibited information?

The output is a decision plus a structured plan and proof. The challenge does not require executing deletion or building a privacy request portal. Its policy is supplied in `deletion_rules.csv`; external regulatory guidance provides context and must not replace those rules. Source: [challenge specification](https://github.com/interviewstreet/hackerrank-orchestrate-october26/blob/main/problem_statement.md).

## 3. Market landscape

The following is a representative capability review, not an exhaustive ranking. Vendor documentation describes available features; it is not independent validation of deployment quality or effectiveness.

| Product/category | Publicly documented capability | What it means for our design | What remains unverified |
|---|---|---|---|
| OneTrust Privacy Rights Automation | Intake, identity verification, discovery, deletion, redaction, and secure response | These are baseline category capabilities; a broad workflow clone is weak positioning | Independent reconstruction of past state across the challenge's mixed artifacts |
| Transcend DSR Automation | Identifier enrichment, dependent preflight checks, legal-hold checks, and request/integration audit events | Identity expansion and dependency handling must be first-class components | Breadth and independence of post-deletion verification for arbitrary evidence |
| DataGrail Request Manager | Multiple-identifier extraction, integration-based discovery and deletion, review stages, retries, and manual completion options | Preserve the distinction between workflow progression and observed resource state | How a particular deployment validates manually completed or skipped work |
| Fides engineering framework | The archived public implementation documents graph-based access and erasure/masking with policy hooks | Reuse the architectural idea of policy-aware dependency traversal | Suitability of the archived public code for a new maintained deployment |
| Storage and analytics platform controls | Platform-specific deletion, version handling, purge, and retention mechanisms | The auditor needs store-specific evidence semantics | A single cross-platform interpretation of deletion cannot be assumed |

Sources: [OneTrust overview](https://www.onetrust.com/products/data-subject-request-dsr-automation/), [Transcend preflight](https://docs.transcend.io/docs/articles/dsr-automation/preflight-and-enrichment/preflight-and-identity-enrichment-overview), [Transcend audit trail](https://docs.transcend.io/docs/articles/security/audit-trail), [DataGrail deletion lifecycle](https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/deletion/), [historical Fidesops execution guide](https://ethyca.github.io/fidesops/guides/fidesops_workflow/).

Important status caveat: the public `ethyca/fides` repository is marked archived as of 28 August 2026. The historical execution guide is useful as an architectural reference, not evidence of current supported product behavior. [Public repository](https://github.com/ethyca/fides).

### Demand signal and limits

DataGrail's June 2025 report announcement states that deletion requests rose 82% year over year in its research. This is a vendor-reported signal of operational demand, not a representative estimate for every company, an independent market-size estimate, or our expected savings. [DataGrail report announcement](https://www.datagrail.io/press/datagrail-report-consumer-demand-for-data-privacy-surges-driving-up-business-costs-as-data-deletion-requests-rise/).

We have not established total addressable market, willingness to pay, competitor pricing, or procurement demand. Those are unnecessary for the challenge and would require further research for a commercial product.

## 4. Documented mechanisms behind ghost data

### A. Hidden versions can survive a successful delete

AWS documents that deleting an object without its version ID in a versioned S3 bucket adds a delete marker rather than permanently removing its versions. Removing that marker can make the object visible again. Therefore, visibility in a normal object lookup and physical removal of all relevant versions are different properties. [AWS deletion behavior](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjects.html).

**Design implication:** record the store and observation scope. A negative lookup proves only what that lookup covers. In this challenge, apply this principle to the actual supplied evidence; do not invent S3 versions that are not present in the corpus.

### B. Logical removal can precede physical purge

Databricks documents that Delta table history preserves older data files, that `VACUUM` removes eligible unreferenced files, and that deletion-vector workflows require purge handling. It also explicitly calls out upstream queues, files, and databases. [Databricks deletion guidance](https://docs.databricks.com/aws/en/ldp/gdpr).

**Design implication:** distinguish current read results, retained history, and upstream sources. A compliant current table does not prove the entire data path is compliant.

### C. Concurrent writes can interfere with deletion

Elasticsearch delete-by-query operates against a snapshot. Changes between the snapshot and deletion can cause version conflicts. [Elasticsearch API documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-delete-by-query.html).

**Design implication:** operation submission and resulting state are separate observations. Investigate later readbacks and processes that can write identifiers back into downstream resources.

### D. Backup handling is a controlled-retention problem

UK ICO guidance explains that erasure can require steps for backups as well as live systems, and that backup data awaiting overwrite may need to be put beyond use. This is jurisdiction-specific context, not the challenge's policy. [ICO right-to-erasure guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/?q=report).

**Design implication:** do not prescribe blanket backup destruction. For the supplied policy, preserve the required archive and verify that affected restore access is blocked. Production use would require organization-specific policy review.

### E. A person has multiple system identifiers

Transcend documents enrichment from one identifier into identifiers needed by other integrations and recommends an immutable unique core identifier. [Transcend platform concepts](https://docs.transcend.io/docs/articles/overview/concepts).

**Design implication:** expand the subject's identity through grounded links before searching evidence. An email-only exact search will miss historical aliases and resources indexed by other keys.

### F. Workflow closure has a defined, limited meaning

DataGrail's documentation permits manual completion of certain processing or failed integrations and defines its final `Closed: Deleted` state in terms of the requester receiving the results email. This does not establish a product defect; it illustrates why the semantics of each status must be understood. [Deletion lifecycle](https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/deletion/).

**Design implication:** the challenge's reported completion field cannot substitute for observed data-state evidence.

## 5. Problem map and proposed priorities

Priorities below reflect the challenge's correctness contract, not measured market prevalence.

| Failure mode | Root cause to investigate | User consequence | Required agent behavior | Priority |
|---|---|---|---|---|
| Unauthorized deletion plan | Access/export/opt-out mistaken for erasure | Wrong action against an active customer | Semantic intent gate with negation and multilingual support | P0 |
| Historical alias missed | Search uses only the request email | Residual identifiers remain undiscovered | Provenance-linked identity expansion | P0 |
| Replica omitted | Primary result treated as global truth | Residual data remains available | Independent replica/store observations | P0 |
| Success claim accepted as proof | Command result conflated with state | False `COMPLETE` verdict | Evidence hierarchy and post-operation readbacks | P0 |
| Sync recreates data | Source or writer remains active | Repeated deletion failure | Dependency discovery; disable relevant flow first | P0 |
| Backup restores erased data | Restore control absent | Previously removed identifiers return | Restore-risk detection and blocking verification | P0 |
| Required record over-deleted | All matches treated identically | Loss of required retained records | Conditional policy evaluation and retention checks | P0 |
| PII hidden in attachments | Structured tables are the only sources searched | Incomplete copy coverage | PDF, image, text and log extraction | P0 |
| Later fix leaks into earlier audit | Capture and observation times ignored | Historically incorrect verdict | Enforce audit cutoff and scope-aware reconciliation | P0 |
| Uncertain evidence silently omitted | Parsing or retrieval failure hidden | Unsupported completion claim | Coverage diagnostics and unresolved-case handling | P0 |
| Reviewer cannot inspect reasoning | Only a verdict is provided | Slow investigation and weak trust | Traceable evidence-to-rule-to-step links | P1 |
| Expensive repeated interpretation | Same global file parsed per case | High run cost and inconsistent extraction | Parse once, index, cache, retrieve narrowly | P1 |

## 6. Proposed product position

**Positioning hypothesis:** “Audit a deletion completion claim against the evidence, identify what remains and what can return, and produce the exact policy-safe steps needed to prove completion.”

Potential initial users are privacy operations reviewers and data/platform engineers investigating failed or disputed requests. A potential budget owner is a privacy or compliance leader; engineering leadership may sponsor technical integrations. These are hypotheses, not validated buyer findings.

The useful differentiators to demonstrate are:

- **Evidence independence:** every decision can be traced to source observations, not merely a task status.
- **Historical reconstruction:** answer what was true at the specified audit time.
- **Durability checks:** include sources and processes that can recreate data.
- **Retention correctness:** prove both removal of prohibited identifiers and availability of required records.
- **Mixed-format investigation:** unify databases, operational traces, documents, and screenshots.

These are proposed areas of emphasis. They must not be presented as unique market capabilities without comparative testing.

## 7. What to build for this challenge

### Core workflow

1. Validate requests and load the supplied policy.
2. Determine whether deletion is authorized.
3. Resolve current and historical identifiers with timestamps and provenance.
4. Parse and index all supplied evidence, keeping observation scope and capture time.
5. Retrieve relevant resources and flows through grounded identity/resource links.
6. Reconstruct eligible state at `audit_at` without treating claims as proof.
7. Compare each record and recreation path with its policy obligations.
8. Generate findings, ordered remediation, and complete verification coverage.
9. Validate schema, operation order, citations, cutoff compliance, and case coverage.
10. Evaluate samples and authored regressions; write the required CSV and reports.

### Use AI where interpretation is needed

AI is appropriate for multilingual intent, document/screenshot interpretation, and extracting relationships from noisy prose. Exact parsing, timestamp comparisons, policy tables, operation ordering, and CSV validation should remain deterministic. An LLM-generated verdict without validated evidence links is insufficient.

An internal observation should contain `subject_links`, `system_id`, `resource_id`, `category`, `observed_at`, `captured_at`, `store_scope`, `record_facts`, `evidence_id`, and extraction diagnostics. Keep lookup/query identifiers distinct from identifiers returned inside a record.

### Proof obligations

| Obligation | Example evidence needed |
|---|---|
| Relevant copy treated correctly | Direct readback, scoped snapshot, or grounded record observation |
| Required identifiers removed | Field-level redaction/anonymization evidence, not a label alone |
| Recreation path controlled | Relevant connector disabled or restore access blocked |
| Retention honored | Required record observed available with permitted identifiers |
| Audit answer historically valid | Both artifact availability and observation timestamps within cutoff |

Completion is bounded by the supplied evidence universe. A prototype cannot prove absence in undisclosed systems or guarantee that future configuration changes will never re-enable a flow.

## 8. Validation and measures

Keep the required public sample metrics from the PRD: status, exact row, step, field, sequence, and citation accuracy. Add these diagnostic measures:

- False-complete rate: true incomplete cases incorrectly marked complete / labeled incomplete cases.
- Unauthorized-plan rate: labeled non-deletion cases receiving steps / labeled non-deletion cases.
- Required-retention violations: proposed destructive actions against required retained records.
- Historical-alias recall and active-flow/restore-risk recall on authored tests.
- Evidence ingestion coverage: supported files successfully inspected / manifest files, plus all extraction failures.
- Unsupported-citation and post-cutoff-citation counts.
- Runtime, calls, tokens, and estimated cost for the final full run.

Do not calculate hidden-case accuracy without labels. High ingestion coverage alone does not prove high fact-extraction recall.

Compare three implementations on the same public samples and custom tests: identifier-only search, a general LLM audit baseline, and the proposed structured evidence/policy pipeline. Use identical eligible evidence and report cost and correctness tradeoffs. This comparison is planned, not yet executed.

## 9. Questions for later customer discovery

Conduct interviews before making commercial claims. Ask privacy reviewers and data engineers to walk through a recent deletion investigation:

1. What evidence lets you mark a request complete? Who signs off?
2. Which systems require manual steps, and where do identity joins fail?
3. Have you seen reappearance after sync or restore? What established the cause?
4. How are retained records, attachments, and old identifiers handled?
5. Can you reconstruct a previous audit date without using later information?
6. What does your current privacy tool verify independently after an action?
7. What time and coordination does a disputed case consume?
8. Would a read-only assurance tool help, and what evidence access would be permitted?

A promising validation result would be repeated, documented pain around assurance that existing configurations do not resolve. If existing tools already solve it reliably, position the work as an integration or specialized audit capability rather than assuming a standalone market.

## 10. Build decision

Proceed with the PRD's offline audit engine, prioritizing correct identity links, timestamp/scope reconstruction, retention-safe policy decisions, and recreation risks. Keep a coverage ledger so the agent knows which proof obligations have and have not been established. Defer a UI and production connectors until the evidence engine passes the required evaluation.

This research supports the technical problem and product direction. It does not establish market size, willingness to pay, competitor deficiencies, production readiness, or completed benchmark results.
