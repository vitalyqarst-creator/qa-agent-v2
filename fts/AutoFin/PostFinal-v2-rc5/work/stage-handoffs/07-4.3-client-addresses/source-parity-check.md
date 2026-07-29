# Source Parity Check: 07-4.3-client-addresses

## Result

- `status`: `blocked-input`
- `scope_slug`: `4-3-client-addresses`
- `checked_sources`: DOCX, XHTML, PDF
- `xhtml_candidates`: `28`
- `pdf_bsr_hits`: `BSR 115-161`, `BSR 324`
- `docx_extraction_status`: `partial`

## Summary

Границы scope подтверждены по XHTML и PDF: строки блока адресов клиента покрывают `BSR 115-161`, а связанное требование `BSR 324` найдено отдельно и должно оставаться cross-reference. DOCX присутствует как source of truth, но машинное извлечение через `python-docx` не показало надежной полноты по строкам `34-58`; поэтому DOCX не отвергается, но требует использования XHTML как обязательного машиночитаемого источника и PDF как structural/visual cross-check.

## Requirement ID Parity

| Requirement code(s) | XHTML | PDF | DOCX extraction | Decision |
|---|---:|---:|---:|---|
| `BSR 115-127` | found | page 20 | partial | in scope |
| `BSR 128-142` | found | page 21 | partial | in scope |
| `BSR 143-161` | found | page 22 | partial | in scope |
| `BSR 324` | found | page 34 | partial | cross-reference in scope |

## Row/Block Parity

| Source row | Field/block | BSR codes | XHTML | PDF | Decision |
|---:|---|---|---:|---:|---|
| 33 | Блок «Адреса клиента» | n/a | found | found near pages 20-22 | context |
| 34 | Адрес регистрации | `BSR 115-120` | found | page 20 | in scope |
| 35 | Ввести вручную / адрес регистрации | `BSR 121-122` | found | page 20 | in scope |
| 36 | Почтовый индекс / адрес регистрации | `BSR 123-124` | found | page 20 | in scope |
| 37 | Регион / адрес регистрации | `BSR 125` | found | page 20 | in scope |
| 38 | Район / адрес регистрации | `BSR 126` | found | page 20 | in scope |
| 39 | Населенный пункт / адрес регистрации | `BSR 127` | found | page 20 | in scope |
| 40 | Город / адрес регистрации | `BSR 128` | found | page 21 | in scope |
| 41 | Улица / адрес регистрации | `BSR 129` | found | page 21 | in scope |
| 42 | Дом / адрес регистрации | `BSR 130` | found | page 21 | in scope |
| 43 | Корпус / адрес регистрации | `BSR 131-132` | found | page 21 | in scope |
| 44 | Квартира / адрес регистрации | `BSR 133-134` | found | page 21 | in scope |
| 45 | Клиент зарегистрирован в частном доме | `BSR 135-137` | found | page 21 | in scope |
| 46 | Адрес фактического места жительства совпадает с адресом регистрации | `BSR 138-139` | found | page 21 | in scope |
| 47 | Адрес фактического места жительства | `BSR 140-145` | found | pages 21-22 | in scope |
| 48 | Клиент проживает в частном доме | `BSR 146-147` | found | page 22 | in scope |
| 49 | Ввести вручную / адрес фактического места жительства | `BSR 148-149` | found | page 22 | in scope |
| 50 | Регион / адрес фактического места жительства | `BSR 150` | found | page 22 | in scope |
| 51 | Район / адрес фактического места жительства | `BSR 151` | found | page 22 | in scope |
| 52 | Населенный пункт / адрес фактического места жительства | `BSR 152` | found | page 22 | in scope |
| 53 | Город / адрес фактического места жительства | `BSR 153` | found | page 22 | in scope |
| 54 | Улица / адрес фактического места жительства | `BSR 154` | found | page 22 | in scope |
| 55 | Дом / адрес фактического места жительства | `BSR 155` | found | page 22 | in scope |
| 56 | Корпус / адрес фактического места жительства | `BSR 156` | found | page 22 | in scope |
| 57 | Квартира / адрес фактического места жительства | `BSR 157-159` | found | page 22 | in scope |
| 58 | Почтовый индекс / адрес фактического места жительства | `BSR 160-161` | found | page 22 | in scope |
| cross-reference | Раскладка адреса DaData и kladr | `BSR 324` | found | page 34 | in scope as cross-reference |

## Parity Risks

- DOCX extraction through `python-docx` is partial for this table. This is an extraction limitation, not evidence that DOCX lacks the rows.
- PDF confirms BSR locations but is not source of truth and must not replace DOCX/XHTML text extraction.
- Cross-reference `BSR 324` was absent from the initial 07 boundary and has now been added to registry and selection artifacts.
