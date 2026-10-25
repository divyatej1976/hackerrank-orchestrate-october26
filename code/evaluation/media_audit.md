# Media extraction audit

Rechecked all 11 screenshots using both cached full-page OCR and versioned spatial OCR, and all 4 PDFs using plain and layout text extraction. These are extracted strings, not corrections inferred from expected answers. No new OCR invocation was needed to inspect the existing text/layout artifacts.

Resource observations, subject links and state are compared below. Other IDs (orders, tickets and statements), short checksum prefixes, and business statuses are context; they are not automatically modeled as deletion resources. None of these media exposes a complete email hash. OCR spelling variants are preserved for review rather than guessed.

## evidence_04 — account_admin_console_20260926.png

SHA-256: `d5c32ca5b6e1a2b4bbe9f5d41835ef1fd5d4f7061dab9067a4f9f88cea3c1861`. Captured: 2026-09-26T11:00:00Z.

- Ids: CS-8538, CS-8S38, CS-8s38, ORD-20265518, ORD-20265762, ORD-2026S762, ORD-2026SS18, account_5762, support_9538
- Emails: haruka.s1838@zoho.com
- Phones: +81 90 7610 2507
- Hashes: None
- Statuses: Delivered, Returned, delivered, returned
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| account_5762 | PRESENT | user_11 | single-subject document |
| support_9538 | IDENTIFIABLE | user_11 | single-subject document |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_09 — search_index_inspector_20260901.png

SHA-256: `75afdb0ae53a4510c83399a70d88073cb4fb2747454095756e4ddad1a8c70605`. Captured: 2026-09-01T06:00:00Z.

- Ids: search_1874, search_428, user_13
- Emails: g.silva76.jr@gmaiI.com, g.silva76.jr@gmail.com, g.silva76@gmaiI.com, g.silva76@gmail.com
- Phones: None
- Hashes: None
- Statuses: None
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| search_1874 | PRESENT | None | unattributed visual resource |
| search_428 | PRESENT | user_13 | row:y=574,x=0.13-0.78 |

Emails outside modeled record contexts: g.silva76.jr@gmaiI.com, g.silva76.jr@gmail.com, g.silva76@gmaiI.com. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_14 — connector_management_console_20260807.png

SHA-256: `e81fabc93ea1b5f4c918d934cdb2bea05d61737adfcc29f281494f5d8ec46355`. Captured: 2026-08-07T08:00:00Z.

- Ids: data_flow_1121, data_flow_9846
- Emails: jain.aditi@gmail.com, lucia-torres@gmail.com
- Phones: None
- Hashes: None
- Statuses: Continuous, Healthy, delivered
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| data_flow_1121 | ACTIVE | user_14 | row:y=574,x=0.13-0.78 |
| data_flow_9846 | ACTIVE | user_15 | row:y=632,x=0.13-0.78 |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_18 — account_history_report_20260718.pdf

SHA-256: `abe1877efe69fb5617a79c0d22df9113372e1e6804f8986b0fd408563ecca448`. Captured: 2026-07-18T11:00:00Z.

- Ids: NST-2026-0718-1842, ORD-20261260, user_18
- Emails: ingrid.dahl@outlook.com
- Phones: None
- Hashes: None
- Statuses: delivered, paid
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| export_1842 | PRESENT | user_18 | catalog-linked media |

Emails outside modeled record contexts: ingrid.dahl@outlook.com. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_19 — analytics_profile_view_20260713.png

SHA-256: `4e4cb259bc2010b622b0c53fe5872258f994fefc23452a83bb27473758693484`. Captured: 2026-07-13T10:00:00Z.

- Ids: analytics_7438, user_20
- Emails: darwish.omar@icloud.com
- Phones: None
- Hashes: None
- Statuses: Completed, active, completed
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| analytics_7438 | IDENTIFIABLE | user_20 | row:y=200,x=0.13-0.78 |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_23 — customer_export_console_20260618.png

SHA-256: `18b95c1bd8b8956e40216df935498a9f3c181ea2a69b5cd6d3c0841a816d5557`. Captured: 2026-06-18T12:00:00Z.

- Ids: export_1258, export_1259, export_1260, export_1261
- Emails: daniel.park@northstar.shop, ingrid.dahl@outlook.com, marcus.lee@northstar.shop, sara.kim@northstar.shop
- Phones: None
- Hashes: None
- Statuses: Collecting, Expired, Packaging, Processing, Ready
- Short checksum/fingerprint context: Checksum / Download Count / Included, Checksum SHA-256 • 41ca09... / export_1258 daniel.park@northstar.shop Ready 16 Jun 09:27 UTC / Download count, SHA-256 • 41ca09m / 0 / Profile • Orders Saved addresses
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| export_1258 | PRESENT | None | unattributed visual resource |
| export_1259 | PRESENT | None | unattributed visual resource |
| export_1260 | PRESENT | user_18 | row:y=632,x=0.13-0.78 |
| export_1261 | PRESENT | None | unattributed visual resource |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_27 — legal_retention_register_20260529.pdf

SHA-256: `0919c931c018565e82502050ee1026918c1baf210c8ba23d2386415dd46efb10`. Captured: 2026-05-29T08:00:00Z.

- Ids: ORD-20264118, ORD-20264207, ORD-20264319, ORD-20264402, ORD-20264511, ORD-20264600, user_08, user_12, user_17, user_21, user_24, user_29
- Emails: None
- Phones: None
- Hashes: None
- Statuses: None
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| tombstone_17 | REDACTED | user_17 | catalog-linked media |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_28 — support_ticket_console_20260524.png

SHA-256: `542b7aec17e6b2f38827896e7eb52c70e4bfaaca22433621be1f80f54884e944`. Captured: 2026-05-24T07:00:00Z.

- Ids: CS-5034, ORD-20265034, SWF-884103, support_1034
- Emails: kagyeman8947@fastmail.com
- Phones: None
- Hashes: None
- Statuses: In transit
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| support_1034 | IDENTIFIABLE | user_22 | single-subject document |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_32 — backup_restore_console_20260429.png

SHA-256: `2c246aa5843bec609b9ddfdf1154cd81e0fd61996f83954735e9856e48c18bf3`. Captured: 2026-04-29T09:00:00Z.

- Ids: backup_9281, backup_9286, backup_9287, backup_9288, backup_9291
- Emails: areed1433@gmaiI.com, areed1433@gmail.com, bluepeakco@outlook.com, miller.logistics@company.com, summit-retail@company.com
- Phones: None
- Hashes: None
- Statuses: Archive, Completed, Healthy
- Short checksum/fingerprint context: Checksum / Last drill / Retention end, Checksum Verified / Last drill 29 Mar 2026 / Retention end 26 Jul 2026, checksum verification Completed /  / Vault Recovery Manager D Search archives, accounts or restore requests... Production Help VR, checksum verification • Completed / Vault Recovery Manager / Production workspace
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| backup_9281 | ACTIVE | None | unattributed visual resource |
| backup_9286 | ACTIVE | None | unattributed visual resource |
| backup_9287 | ACTIVE | user_16 | row:y=688,x=0.13-0.78 |
| backup_9288 | ACTIVE | None | unattributed visual resource |
| backup_9291 | ACTIVE | None | unattributed visual resource |

Emails outside modeled record contexts: areed1433@gmaiI.com. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_37 — security_audit_explorer_20260905.png

SHA-256: `ca59f693f4e7002466b3fdeaf1bb6763618770963dd811b60003772d07b4b03b`. Captured: 2026-09-05T07:00:00Z.

- Ids: audit_record_002, audit_record_003, audit_record_006, user 03, user_03
- Emails: None
- Phones: None
- Hashes: None
- Statuses: Valid, completed
- Short checksum/fingerprint context: fingerprint / signature / journal, fingerprint 8fOcm31ad / D 22 Aug 11:27 Email change confirmed Profile update user 03 User (self) Valid audit_record_006 / signature Valid
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| audit_record_002 | PRESENT | user_03 | row:y=632,x=0.13-0.78 |
| audit_record_003 | PRESENT | user_03 | row:y=574,x=0.13-0.78 |
| audit_record_006 | PRESENT | user_03 | row:y=746,x=0.13-0.78 |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_42 — deleted_account_reference_20260310.png

SHA-256: `68c28a72afd6ed184d5990d15c543f8a516face204f0360f732755a8a63c28be`. Captured: 2026-03-10T06:00:00Z.

- Ids: CS-3245, CS-3378, FIN-7742, ORD-20263245, user 17, user_17
- Emails: None
- Phones: None
- Hashes: None
- Statuses: Active, Retained
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| tombstone_17 | REDACTED | user_17 | catalog-linked media |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_46 — object_storage_browser_20260213.png

SHA-256: `96e9a191380c29b9e0ab997007268c4cd6353cb6721ebd1ed4a32599d8d37e04`. Captured: 2026-02-13T08:00:00Z.

- Ids: None
- Emails: None
- Phones: None
- Hashes: None
- Statuses: None
- Short checksum/fingerprint context: Checksum / Uploader / Modified, Checksum e71b6d.„ / return_label_4876.pdf 198 KB 11 Feb 16:05 Standard / Uploader support-service
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| object_19 | PRESENT | user_07 | catalog-linked media |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_55 — security_retention_extract.pdf

SHA-256: `8a6428a899dc8d0769048c8e6f6db70c614fe65fd1e0bb87a43c7927c27ecdda`. Captured: 2026-09-05T06:30:00Z.

- Ids: CJX-20260905-0630, audit_record_003, user_03
- Emails: None
- Phones: None
- Hashes: None
- Statuses: valid
- Short checksum/fingerprint context:  Detail                                short fingerprint 8f0c…31ad, short fingerprint 8f0c…31ad /  / COMPLIANCE JOURNAL - SIGNED RECORD EXTRACT
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| audit_record_003 | PRESENT | user_03 | single-subject document |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_58 — delivery_correction_attachment.pdf

SHA-256: `0c58960759d4821b030b467d6fe531e83e38e7f50b3de3389a735521d0001f18`. Captured: 2026-09-12T07:30:00Z.

- Ids: CS-4827, ORD-20264827, support_001
- Emails: priya.raman@gmail.com
- Phones: +91 98765 73142
- Hashes: None
- Statuses: None
- Short checksum/fingerprint context:  Detail                           checksum prefix c90a42, checksum prefix c90a42 /  / DELIVERY ADDRESS CORRECTION REQUEST
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| support_001 | PRESENT | user_07 | single-subject document |

Emails outside modeled record contexts: None. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## evidence_60 — marketing_profile_console.png

SHA-256: `51fa0e6a38f8fa3629ba1b0d0b90b4ed139715956b97bfd09a6f1a6232c15df5`. Captured: 2026-09-16T07:20:00Z.

- Ids: marketing_001
- Emails: sj.park@naver.com
- Phones: +8210-5837-9451
- Hashes: None
- Statuses: Live, live
- Short checksum/fingerprint context: None
- Recognized resource IDs dropped by ingestion: None

| Extracted resource | Engine state | Subject links | Locator |
|---|---|---|---|
| marketing_001 | PRESENT | None | unattributed visual resource |

Emails outside modeled record contexts: sj.park@naver.com. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.

## Findings and fixes

- Fixed the page-to-row fallback: a row exposing an unknown email no longer inherits the sole recognized customer elsewhere on the page. This removed false media ownership of search_1874 and export_1258/1259/1261. Known customer headers still link single-customer documents.
- Status classification now reads the selected resource context. A disabled/blocked label or email elsewhere on a multi-customer page cannot determine another resource’s state.
- Plain OCR misreads user_11 as user_ll (evidence_04), gmail as gmaiI (evidence_09/32), and numeric backup IDs (evidence_32). Spatial OCR recovers the useful email/resource rows; the correct account link is independently grounded by the visible email. No fuzzy identifier substitution is used.
- Visual inspection of evidence_37 confirms audit_record_001, audit_record_004 and audit_record_005 as well as the three IDs OCR recognizes. Both OCR passes drop those three small reference strings. They are not synthesized into inference. The image is captured after the affected sample cutoff, so it cannot prove earlier state. This remains an OCR coverage limitation.
- Evidence_60 exposes sj.park@naver.com and +8210-5837-9451 but the supplied identity catalog links marketing_001 to a different subject. The literal content is preserved; no new subject is fabricated from this conflict.
- PDFs preserve the visible user references, emails, phone and retention details in extracted text. Opaque statement/tombstone/object names require explicit catalog aliases, not ID arithmetic.

Coverage: 11 screenshots; 4 PDFs. Sample metrics after the extraction fix are unchanged; no missing sample ownership link is supplied by these media.
