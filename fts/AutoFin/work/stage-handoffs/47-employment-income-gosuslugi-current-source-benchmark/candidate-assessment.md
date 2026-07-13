# Employment Benchmark Candidate Assessment

## Источники

- Current FT family: `source/FT4AutoFinFinal.docx|xhtml|pdf`.
- XHTML boundary: table `6`, rows `103`–`127`.
- Requirement codes: `BSR 264`–`BSR 310`.
- PDF boundary: pages `30`–`34`, до блока `Визуальная информация`.
- Relevant mockups opened: Figure 3 employment/Gosuslugi state and Figure 5 maximum application state.

## Source blockers

| blocker_id | source_anchor | observation | impact |
| --- | --- | --- | --- |
| `EMP-BLK-001` | XHTML table 6 rows 106–114; `BSR 265`, `268`, `270`, `272`, `275`–`284` | Visibility conditions reference field `Тип занятости`, while the only driver row and mockup label are `Социальный статус`; FT does not define them as aliases. | Conditional test steps cannot select the source-backed driver without inventing an alias. |
| `EMP-BLK-002` | XHTML rows 105/107; support dictionaries `Социальный статус` and `ОПФ` | Main FT and support file expose different value sets: support adds `безработный`, while FT and support materially diverge on `ОПФ`. | Closed-set dictionary obligations cannot be compiled without a source decision. |
| `EMP-BLK-003` | `BSR 298` | Gosuslugi technical behavior is delegated to an absent separate document. | UI-visible selection/text can be covered, but request/result/error assertions remain unavailable. |

## Решение

Candidate отклонён для текущего speed benchmark. `EMP-BLK-001/002` делают writer outcome зависимым от продуктового уточнения, поэтому запуск измерял бы обход source ambiguity, а не качество и скорость standard pipeline.

Historical H13 artifacts остаются недопустимыми как requirements evidence: они основаны на `AutoFinPreFinal` и имеют устаревшие BSR anchors.
