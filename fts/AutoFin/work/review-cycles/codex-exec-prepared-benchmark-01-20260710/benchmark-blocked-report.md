# Prepared fast-path benchmark: остановка на прогоне 1/3

## Итог

- Benchmark run `1/3` остановлен со статусом `blocked-obligation-gate`.
- Runs `2/3` и `3/3` не запускались по stop rule.
- Writer создал структурно валидный draft и покрыл все `3/3` testable obligations.
- Seed, structure и evidence-access gates прошли.
- Reviewer не запускался.
- Promotion выключен; production test case не создан.

## Метрики run 1

| показатель | результат |
| --- | ---: |
| writer first meaningful artifact | `80.750 s` |
| writer duration | `99.093 s` |
| writer commands | `3 / 8` |
| test cases | `3` |
| testable obligations covered | `3 / 3` |
| reviewer | не запускался |

## Реальный blocker

Draft корректно вынес `ATOM-PREP-004` со статусом `gap` в отдельный set-level раздел `## Coverage gaps` после последнего `TC-PREP-003`. Однако `obligation_gate.py` определяет конец TC-блока только по следующему заголовку `TC-*`. Для последнего кейса блок ошибочно продолжается до конца файла, поэтому поле `**Трассировка:** ATOM-PREP-004` из последующего gap-раздела было приписано к `TC-PREP-003`.

Gate выдал ложный finding `non-testable-obligation-used-as-test`, хотя сам TC явно говорит, что внутренняя интерпретация `NULL` не проверяется.

Canary v4 прошёл случайно: его set-level gap traceability имела Markdown bullet перед bold-полем, который не совпал с текущим регулярным выражением. Различие форматирования выявило нестабильную границу TC parser-а.

## Требуемый фикс

1. Завершать TC-блок на следующем Markdown heading того же или более высокого уровня, а не только на следующем `TC-*`.
2. Оставлять вложенные headings более низкого уровня внутри TC.
3. Добавить regression fixtures для последнего TC, после которого идут `Coverage gaps`, `Неисполняемые границы покрытия` и другие set-level разделы.
4. Проверить варианты traceability с bullet и без bullet.
5. После локальных gates повторить новый canary и benchmark в новых immutable cycles.

## Readiness

Текущий статус: `experimental-only`. Reviewer fast path и schema compatibility доказаны, но end-to-end benchmark пока нельзя считать завершённым из-за ложноположительного deterministic writer gate.
