# Source Parity Check — Questionnaire Upload Transfer V8 Prod Candidate

## Контекст

- DOCX source of truth: `source/FT4AutoFinFinal.docx`.
- XHTML extraction source: `source/FT4AutoFinFinal.xhtml`.
- PDF structural cross-check: `source/FT4AutoFinFinal.pdf`, страницы 26–27.

## Identity

| source | SHA-256 | locator |
| --- | --- | --- |
| DOCX | `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b` | table 6, rows 81–82 |
| XHTML | `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66` | table rows 134–135 |
| PDF | `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58` | pages 26–27 |

## Parity Result

| item | DOCX | XHTML | PDF | result |
| --- | --- | --- | --- | --- |
| Информационное поле | always visible; informational; `О=Да`, `Р=Нет` | `BSR 206`; `BSR 207` | codes and row visible on p.26 | match |
| Анкета клиента upload | picker, DnD, QR; one file/type; jpg/png/pdf; max 40 МБ; exact error; filename; archive | `BSR 208–212` | `BSR 208–211` on p.26; continuation and `BSR 212` on p.27 | match |

## Code Recovery

- DOCX сохраняет поведение, но не BSR labels.
- XHTML и PDF согласованно восстанавливают `BSR 206–212`; коды обязательны в traceability.
- Legacy `AutoFinPreFinal` mapping отклонён.

## Visual Check

- H56 visual check страниц 26–27 подтверждён теми же source hashes;
- структурного расхождения, влияющего на scope, нет.
