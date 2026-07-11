## Coverage Gaps

| gap_id | source_refs | dimension | description | impact | status | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- |
| GAP-001 | BSR 202; BSR 207; BSR 215 | file-upload-duplicate-technical-error | Source defines one-file-per-type, allowed formats, size limit and common validation error text. It does not define exact UI behavior for attempting to attach a second file to the same document type or separate technical upload failures. | non-blocking | open | ATOM-030 |
| GAP-002 | BSR 229 | async/mobile | Source defines QR popup and that QR contains a mobile upload link, but not QR expiry, mobile upload completion result or async status in the application. | non-blocking | open | ATOM-041 |
| GAP-003 | BSR 232 | print-form-content | Download action is in scope; PDF template/content/data-with-consents validation requires section 4.4 / print-form requirements and is not executable inside this scope alone. | non-blocking | open | ATOM-044 |
| coverage_gap:wr-004 | BSR 212; BSR 217; BSR 226 | archive-internal | Closed by evidence-based archive checks for questionnaire, passport and second document. | non-blocking | closed-by-tc | ATOM-012; ATOM-019; ATOM-029; TC-AF-DOC-029; TC-AF-DOC-030; TC-AF-DOC-031 |
| coverage_gap:wr-005 | BSR 225 | external-program-rule | Closed by explicit branch TC for non-GOS, GOS and инвалидов second-document requiredness. | non-blocking | closed-by-tc | ATOM-028; TC-AF-DOC-028 |
| GAP-WR-006 | BSR 222 | date-invalid-enforcement | The source defines that the date must not exceed the current date; the exact UI rejection mechanism/message is not defined. Legacy alias: `coverage_gap:wr-006`. | non-blocking | open | ATOM-034 |
| GAP-WR-007 | BSR 227 | role-archive-access | Archived-document role access matrix and access path are not defined in this scope. Legacy alias: `coverage_gap:wr-007`. | non-blocking | open | ATOM-039 |
