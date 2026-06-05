# Experience-based Coverage Format

`experience-based-charter.md` - необязательный post-baseline artifact для `error guessing`, exploratory/session charters и проверок на основе известных дефектов продукта. Он создается только после FT-first baseline: source extraction, obligations, plan, TC и gaps не должны зависеть от exploratory assumptions.

## Experience-based Charter

| charter_id | target_area | hypothesis_or_defect_pattern | source_of_experience | suggested_checks | timebox | result | promoted_to |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EXP-001` | `Раздел Сведения о занятости` | `Поля суммы часто ошибочно принимают разделители и знак` | `test-design-defect-taxonomy.md; prior reviewer findings` | `Проверить пробел, запятую, минус, спецсимвол` | `30 min` | `2 gaps, 1 source-backed obligation` | `OBL-...; GAP-...` |

## Rules

- Charter не является источником требований и не создает executable baseline `TC-*` без source-backed oracle или approved clarification.
- Найденная идея должна быть классифицирована как `source-backed obligation`, `approved clarification`, `coverage gap`, `out-of-scope` или `discarded`.
- Experience-based checks могут становиться exploratory notes, eval candidates или уточняющими вопросами, но не должны скрывать FT-first coverage gaps.
- Для repeatable defects обновляй `test-design-defect-taxonomy.md` и eval candidate, если дефект можно воспроизводимо проверять.

