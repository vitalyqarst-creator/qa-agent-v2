# Source-backed проверка V7 diagnostics

## Статус входа

- V7 является immutable terminal evidence со статусом `blocked-invalid-output`; его reviewer-ответ не считается sign-off и не используется как источник требований.
- Проверенный V7 draft: `work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`, SHA-256 `17c9bd80c2cff3d19939831f9d42503aebdbd10dc9268d98299896e98dbac23e`.
- Источник предметной проверки: V8 compiler inputs, полученные из проверенного V7 source package и уточнённые только в подтверждённых строках design plan/obligation table.

## Решения по диагностическим findings

| diagnostic | решение | проверяемое основание | действие V8 |
| --- | --- | --- | --- |
| `F-001` mixed package id | подтверждён как process metadata defect | V7 содержит package id V6 в сохранённых секциях и V7 в replacement; это не изменение FT-семантики | runner-owned миграция только строки `package_id`; отдельные byte- и normalized-semantic hashes; metadata gate до reviewer |
| `F-002` DICT values absent | отклонён | V7 `source-evidence.md`, блок `DICT-001`, явно содержит активные `Мужчина` и `Женщина`; потеря произошла в compact reviewer projection | не включать TC в repair set; передавать структурированный `dictionary_evidence.active_values` |
| `F-003` ambiguous FIO action | подтверждён для `TC-ACPD-012` | `OBL-027`/`ATOM-020`, `SRC-006.P02`, `BSR 59` требуют наблюдаемого изменения `Пол`; V7 шаг не называет конкретное поле ввода | design plan теперь фиксирует ввод префикса именно в `Фамилия` и сравнение с полом выбранного runtime-варианта |
| `F-004` non-observable boundary oracle | подтверждён для `TC-ACPD-014`, `TC-ACPD-015` | `OBL-030/035` и `OBL-033/036`, `SRC-007.P02/P04/P05`, `BSR 61-63`; V7 expected повторяет правило границы без видимого post-state | фиксировать `D`, вычислять границу, завершать ввод и сравнивать видимое логическое значение `Дата рождения` с введённой датой |
| `F-005` missing branch precondition | подтверждён для 10 TC | `SRC-009.P01`, `SRC-010.P01`, `SRC-011.P01`; `BSR 66,70,74`: previous-FIO поля доступны только при `Клиент менял ФИО=Да` | каждый целевой design row явно устанавливает `Да` и проверяет видимость поля до ввода/подсказки |

## Bounded repair set

Ремонтируются только следующие 13 TC:

`TC-ACPD-012`, `TC-ACPD-014`, `TC-ACPD-015`, `TC-ACPD-034`, `TC-ACPD-037`, `TC-ACPD-038`, `TC-ACPD-039`, `TC-ACPD-040`, `TC-ACPD-042`, `TC-ACPD-043`, `TC-ACPD-044`, `TC-ACPD-045`, `TC-ACPD-046`.

Остальные 34 TC не являются writer-target. Для них допустима только runner-owned замена единственной строки `package_id` с доказательством неизменности остального содержимого секции.

## Сохранённые границы

- `GAP-001`, `GAP-002`, `GAP-003` остаются non-blocking и не получают выдуманной UI-конкретики.
- DaData success paths используют runtime-selected значения; конкретный порядок/литералы динамических подсказок не фиксируются как постоянные.
- FT-first baseline не изменяется; V8 остаётся unsigned до независимого reviewer sign-off.
