# Пробелы Покрытия Scope

## Контекст

- `scope_slug`: `application-card-calculator-summary-entrypoints`
- Основной FT: `source/FT4AutoFinFinal.docx`
- Machine-readable source: `source/FT4AutoFinFinal.xhtml`, row 55, `BSR 46`.

## Summary

- Найдено gaps: `1`
- Есть blocking gaps: `no`
- Writing можно стартовать: `partial`, после passed `scope_gap_review`.

## Coverage Gaps

### GAP-001
**FT Reference:** `section 4.3 / table 4 / SRC-002 / BSR 46 / PDF page 16`
**Source Path:** `source/FT4AutoFinFinal.docx`; `source/FT4AutoFinFinal.xhtml`; `source/FT4AutoFinFinal.pdf`
**Related Atomic Statement(s):** `ATOM-005`; `ATOM-006`
**Source Statement:** При нажатии открывается окно кредитного калькулятора с предзаполненными данными заявки; подробное описание вынесено во внешнее ФТ `Калькулятор`.
**Gap Type:** `cross-ft-dependency`
**Description:** Точный состав предзаполненных полей и соответствие каждого значения данным заявки не определены доступным Final ФТ.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `ATOM-006`
**Missing Behavior:** Исчерпывающий перечень полей и exact value mapping.
**Why Expected Result Not Derivable:** `BSR 46` подтверждает наличие предзаполненных данных, но не перечисляет поля и правила соответствия.
**Affected Test-design Dimension:** `expected-result`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** exact field/value mapping
**Why Not Executable:** Нельзя определить полный expected result без внешнего ФТ `Калькулятор`.
**Downstream Do Not Test:** Полноту набора prefill-полей, точный mapping, расчёты и внутреннее поведение калькулятора.
**Risk:** `medium`
**Blocks Ready For Review:** `no`
**Question To Analyst:** Предоставить внешнее ФТ `Калькулятор`, если требуется полная проверка mapping.
**Temporary Handling:** Отдельно проверить открытие окна и наблюдаемое наличие хотя бы одного предзаполненного data-bearing значения до пользовательского ввода; не утверждать полноту.
**Writer Rule:** Создать исполнимые кейсы только для открытия и наличия prefill; сохранить exact mapping как gap.
**Reviewer Rule:** Отклонить любой кейс, который объявляет полный mapping покрытым без нового источника.
**Needs User Input:** `no`
**Status:** `open`

## Accepted-risk Deferral

- Не требуется: gap изначально non-blocking и должен пройти pre-writer `scope_gap_review`.

## Что Можно Покрывать Несмотря На Gaps

- Постоянную видимость виджета.
- Пять отображаемых параметров и соответствие их значений сохранённым данным того же этапа и заявки.
- Переход по виджету.
- Открытие окна и наблюдаемое наличие prefill до пользовательского ввода.

## Что Нельзя Домысливать

- Полный состав полей, exact mapping, расчётные правила, пустые/непустые значения и поведение внешнего калькулятора.

## Требуемые Уточнения

- См. `scope-clarification-requests.md`; активный вопрос пользователю не требуется для ограниченного покрытия.
