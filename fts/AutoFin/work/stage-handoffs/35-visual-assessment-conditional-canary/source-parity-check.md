# Source Parity Check

## Контекст

- Source set: `FT4AutoFinFinal.docx`, `FT4AutoFinFinal.xhtml`, `FT4AutoFinFinal.pdf`.
- Current design anchors: `work/test-design/section-18-visual-assessment-criteria/source-row-inventory.md` и `source-table-normalization.md`.
- Проверяемые коды: `BSR 312`, `BSR 313`, `BSR 314`, `BSR 315`, `BSR 316`, `BSR 317`.

## Результат

| проверка | результат |
| --- | --- |
| XHTML содержит выбранные Table 4 свойства и Appendix 1 values | `pass` |
| PDF подтверждает Final BSR-коды и структуру | `pass` |
| DOCX сохранён как source of truth | `pass` |
| Старые PreFinal-коды `BSR 304–309` исключены из canary | `pass` |
| Blocking parity issue | `none` |

## Ограничения

- Appendix 1 используется только для конкретных fixtures `DICT-101`.
- PDF не является источником нового поведения.
