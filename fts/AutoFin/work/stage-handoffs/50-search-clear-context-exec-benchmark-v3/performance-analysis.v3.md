# Search Clear Context V3 Performance Analysis

## Сравнение

| metric | V2 prepared `codex exec` | V3 prepared `codex exec` | вывод |
| --- | ---: | ---: | --- |
| time to terminal | `71.985 s` | `13.453 s` | V3 остановлен рано; это не ускорение успешного cycle |
| writer | `34.610 s`, draft-ready | `13.453 s`, blocked-input | Новый draft не создан |
| reviewer | `37.375 s`, changes-required | not started | Semantic quality и session isolation не измерены |
| stages | `2` | `1` | V3 закрыт до reviewer |
| commands/file changes by stages | `0 / 0` | `0 / 0` | Read-only compact boundary сохранился |
| total tokens | `42,721` | `20,160` | Меньше только из-за ранней остановки |
| test cases | `4` | `0` | Стоимость на TC для V3 не рассчитывается |

## V3 Context

- Primary writer context: `26,465` bytes.
- Prompt bytes: `22,232`; instruction bytes: `4,233`; one instruction artifact.
- Writer input/output: `20,026 / 134` tokens; total `20,160`.
- First output: approximately `0.344 s`; no tool commands and no stage file mutations.
- Validator invocations: `0 / 5`, because no draft reached materialization or gates.

## Вывод

V3 не даёт положительного performance result. Он даёт полезную failure attribution: примерно за 13.5 секунд система точно остановила несогласованный runtime contract без retry и production mutation. Сравнение скорости и токенов writer→reviewer нужно повторить только в новом V4.
