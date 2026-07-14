# Source Row Inventory — Questionnaire Upload Transfer V6

## Source Row Inventory

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-QUT-001` | `WP-QUT-01` | `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку`; `О=Да`; `Р=Нет`; text/string | `DOCX table 6 row 81; XHTML row 134; PDF p.26` | `BSR 206; BSR 207` | `yes` | `ATOM-001; ATOM-002` |
| `SRC-QUT-002` | `WP-QUT-01` | `Анкета клиента`; `О=Да`; `Р=Нет`; file upload/binary | `DOCX table 6 row 82; XHTML row 135; PDF pp.26-27` | `BSR 208; BSR 209; BSR 210; BSR 211; BSR 212` | `yes` | `ATOM-003; ATOM-004; ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011` |

## Inventory Notes

- Каждый in-scope clause имеет отдельный `SRC-QUT-*.P*` в scope contract.
- `О` и `Р` интерпретируются только через обязательный `AGENT-NOTES.md`.
- Старый `work/test-design/14-application-card-documents-and-questionnaire-files` не является source evidence из-за Final/PreFinal drift.
