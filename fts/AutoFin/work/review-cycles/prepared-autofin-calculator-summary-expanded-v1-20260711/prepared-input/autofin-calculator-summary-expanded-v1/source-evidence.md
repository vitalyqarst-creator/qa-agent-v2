# Prepared Source Evidence

- package_id: `autofin-calculator-summary-expanded-v1`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-calculator-summary-expanded-v1-20260711/prepared-input/.autofin-calculator-summary-expanded-v1.compiled-evidence.md`
- source_sha256: `106164d9e5d1256f8c01fa2cb6bdda61f4379be19d5b0f4c09c1010231cc1607`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## OBL-001

- obligation: OBL-001 | WP-01 | SP-001 | ATOM-001 | field-property | visibility-always | Виджет `Краткая информация с калькулятора` отображается в карточке заявки. | SRC-001`; `BSR 35 | TC-ACCS-001 | covered | Прямая visibility obligation.
- atom: ATOM-001 | WP-01 | SP-001 | BSR 35 | SRC-001 | Виджет `Краткая информация с калькулятора` виден в карточке заявки всегда. | covered | TC-ACCS-001 | TC-ACCS-001 | none_required:covered | -

- plan: PLAN-001 | WP-01 | visibility | SRC-001`; `BSR 35 | ATOM-001 | Открыть карточку заявки и проверить наличие виджета. | positive | visibility-always | existing-application-card | Виджет отображается. | FT row | TC-ACCS-001 | covered

## OBL-002

- obligation: OBL-002 | WP-01 | SP-002 | ATOM-002 | table-list | calculator-summary-fields | Виджет отображает пять перечисленных параметров калькулятора. | SRC-001`; `BSR 36 | TC-ACCS-002 | covered | Состав полей явно задан ФТ.
- atom: ATOM-002 | WP-01 | SP-002 | BSR 36 | SRC-001 | Виджет отображает краткую информацию с этапа `Кредитный калькулятор`: `Сумма кредита, Р`, `VIN`, `Ставка, %`, `Платеж в месяц, Р`, `Срок, мес.`. | covered | TC-ACCS-002 | TC-ACCS-002 | none_required:covered | -

- plan: PLAN-002 | WP-01 | summary-content | SRC-001`; `BSR 36 | ATOM-002 | Проверить состав краткой информации по тестовой заявке. | positive | summary-parameter-list | application-with-calculator-values | Виджет отображает пять перечисленных параметров. | FT row | TC-ACCS-002 | covered

## OBL-003

- obligation: OBL-003 | WP-01 | SP-003 | ATOM-003 | action-navigation | widget-navigation-target-opened | Нажатие виджета открывает этап `Кредитный калькулятор`. | SRC-001`; `BSR 37 | TC-ACCS-003 | covered | `GAP-001` исключает внутреннее поведение калькулятора.
- atom: ATOM-003 | WP-01 | SP-003 | BSR 37 | SRC-001 | При нажатии на виджет выполняется переход на этап `Кредитный калькулятор`. | covered | TC-ACCS-003 | TC-ACCS-003 | none_required:covered | GAP-001

- plan: PLAN-003 | WP-01 | widget-action | SRC-001`; `BSR 37 | ATOM-003 | Нажать на виджет. | positive | navigation-target-opened | click-widget | Открыт этап `Кредитный калькулятор`. | FT row | TC-ACCS-003`; `GAP-001 | covered

## OBL-004

- obligation: OBL-004 | WP-01 | SP-004 | ATOM-004 | action-navigation | calculator-window-prefilled | Кнопка `Кредитный калькулятор` открывает окно с предзаполненными данными заявки. | SRC-002`; `BSR 38 | TC-ACCS-004 | covered | `GAP-001` исключает exact mapping внешнего ФТ.
- atom: ATOM-004 | WP-01 | SP-004 | BSR 38 | SRC-002 | При нажатии на кнопку `Кредитный калькулятор` открывается окно `Кредитный калькулятор` с предзаполненными данными по заявке. | covered | TC-ACCS-004 | TC-ACCS-004 | none_required:covered | GAP-001

- plan: PLAN-004 | WP-01 | button-action | SRC-002`; `BSR 38 | ATOM-004 | Нажать кнопку `Кредитный калькулятор`. | positive | window-open-prefilled | click-button | Открыто окно `Кредитный калькулятор` с предзаполненными данными. | FT row | TC-ACCS-004`; `GAP-001 | covered

## GAP-001

source_refs: ATOM-003; ATOM-004
Неопределённость зафиксирована в coverage gaps.
Do not test calculator screen, calculations, offer selection or exact prefill mapping without external FT `Калькулятор`.
