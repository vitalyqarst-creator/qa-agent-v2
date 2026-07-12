# Итоги shadow-итерации для section 4.3

## Результат

- Независимо от старых тест-кейсов подготовлена eval-only проекция 15 статических obligations для `Фамилия`, `Имя`, `Отчество`.
- Compiler выбрал `simple-field-property`: 15 obligations, 0 gaps, 0 unsupported dimensions.
- Backend dispatcher выбрал проверенный `codex exec`; SDK fallback не разрешался и не использовался.
- Первый immutable cycle остановился как `blocked-input`: prepared plan не содержал конкретного synthetic fixture для шести проверок ввода.
- После явной материализации значения `Тест`, допустимого по `BSR 48`, `BSR 51`, `BSR 54`, новый immutable cycle завершился как `accepted-not-promoted`.
- Writer и reviewer использовали отдельные backend session IDs, не выполняли команд и не изменяли файлы workspace.
- Production target отсутствовал до и после запуска; promotion выключен.

## Метрики успешного cycle

| metric | value |
| --- | ---: |
| Полное время writer + reviewer | 95.172 с |
| Total tokens | 55 189 |
| Uncached input tokens | 50 915 |
| Writer | 64.734 с / 27 773 tokens |
| Reviewer | 30.438 с / 27 416 tokens |
| Validator invocations | 1 |
| Команды / file changes внутри стадий | 0 / 0 |
| Test cases / covered obligations | 15 / 15 |

Неуспешный диагностический cycle дополнительно потратил 15.859 с и 25 091 token. Этот overhead вызван отсутствием materialized fixture и должен устраняться preflight-gate до live exec.

## Качество и сравнение с прежним draft

Старый `writer-r2-draft.md` был прочитан только после независимой генерации и только для post-run сравнения; requirement evidence из него не извлекалось.

| check | Новый shadow draft | Прежний full-scope draft |
| --- | ---: | ---: |
| TC count | 15 | 47 |
| Unique titles | 15 | 39 |
| Duplicate-title groups | 0 | 7 |
| Reviewer result | accepted | round-cap-reached |

Старый cycle не содержит сопоставимого `stage-metrics.ndjson`, поэтому честное сравнение времени и token cost с ним невозможно. Сравнивать абсолютные значения с full-scope draft также методологически неверно: scope различается.

## Критическая оценка

Итерация доказала, что отдельные exec-сессии быстро передают компактный prepared package и дают accepted draft без production write. При этом выявлены два process finding:

1. Prepared compiler проверяет наличие obligation/oracle, но не требует concrete fixture для input-based checks. Из-за этого реальный blocker обнаруживается только дорогим live writer.
2. Reviewer принимает разные obligations `editability` и `value-type`, даже когда их шаги и ожидаемые результаты практически совпадают. Пары `TC-PREP-003/005`, `008/010`, `013/015` требуют будущего semantic-overlap gate или явной политики объединения.

## План второй итерации (выполнен)

- добавить compiler preflight `input-fixture-required` для планов, где действие содержит ввод;
- добавить deterministic semantic-overlap diagnostic для одинаковых step/oracle bodies при разных titles;
- повторить тот же scope и доказать отсутствие failed-cycle overhead и обоснованное объединение либо сохранение overlapping cases;
- production baseline не менять до отдельного решения пользователя.

## Проверки репозитория

- 36 unit tests compiler/dispatcher: pass.
- Полный AutoFin validator в strict/audit-профиле: 0 findings в handoff `30` и обоих shadow cycle; в остальном пакете остаются 78 errors, 2707 warnings и 131 info из унаследованных артефактов вне этой итерации.

## Вторая оптимизационная итерация

Реализованы три связанных изменения процесса:

1. Compiler preflight `input-fixture-required` останавливает input-based plan без concrete fixture до live `codex exec`.
2. Runner создаёт неблокирующий `semantic-overlap-diagnostic.json`, нормализует шаги и итоговый expected result и передаёт найденные группы reviewer-у.
3. Optional `planned_test_case_id` сохраняет полную `OBL -> ATOM` трассировку, но позволяет нескольким obligations использовать один обоснованный наблюдаемый TC. Старые package v5 без поля остаются читаемыми.

### Контрольные cycle

| cycle | result | доказательство |
| --- | --- | --- |
| V3 | `changes-required` | reviewer обнаружил overlap, но literal diagnostic его пропустил |
| V4 | `changes-required` | исправленный diagnostic детерминированно нашёл 3 группы |
| V5 | `blocked-validator` | группировка дала 12 TC, но оставила разрывы в нумерации |
| V6 | `accepted-not-promoted` | 15 obligations покрыты 12 непрерывными TC; overlap findings 0 |

### Сравнение устойчивого результата

| metric | V2 до оптимизации | V6 после оптимизации | изменение |
| --- | ---: | ---: | ---: |
| Test cases | 15 | 12 | −20.0% |
| Covered obligations | 15 | 15 | без потери |
| Cycle duration | 95.172 с | 90.031 с | −5.4% |
| Total tokens | 55 189 | 54 291 | −1.6% |
| Duplicate/overlap groups | 3 вручную | 0 deterministic | закрыто |
| Reviewer | accepted с пропущенным overlap | accepted после объединения | качественно корректнее |

Экспериментальные V3–V5 являются стоимостью разработки gate, а не steady-state стоимостью будущего запуска. Production baseline и shadow target не создавались.

## Следующий рекомендуемый scope

Перейти к ограничениям допустимых символов `BSR 48`, `BSR 51`, `BSR 54`. Это небольшой, но уже `standard-required` scope; он проверит оптимизированный транспорт на негативных классах и UI-calibration gaps без смешивания с DaData.
