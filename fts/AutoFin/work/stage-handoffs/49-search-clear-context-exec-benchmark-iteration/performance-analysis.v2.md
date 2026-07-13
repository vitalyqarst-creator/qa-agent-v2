# Search Clear Context V2 Performance Analysis

## Сравнение

| metric | Historical H19 SDK | V2 prepared `codex exec` | вывод |
| --- | ---: | ---: | --- |
| time to terminal | `>900 s`, writer timeout | `71.985 s` | примерно `12.5x` быстрее до actionable terminal |
| writer | timeout after `900 s` | `34.610 s`, draft-ready | transport/completion problem resolved for this small scope |
| reviewer | not cleanly reached | `37.375 s`, changes-required | fresh semantic review completed |
| sessions | writer timeout path | 2 distinct fresh ids | isolation proven |
| commands/file changes by stages | not comparable | `0 / 0` | compact inline transport worked |
| total tokens | unavailable | `42,721` | still expensive for four obligations |
| uncached tokens per obligation | unavailable | `10,035.5` | next optimization target |

## V2 Context

- Primary context: `50,718` bytes total.
- Prompt bytes: `43,408`; instruction bytes: `7,310`; two instruction artifacts.
- Writer tokens: `21,203`; reviewer tokens: `21,518`.
- Four test cases and four testable obligations.
- Validator invocations: `1 / 5` budget.

## Вывод

Скорость и отдельные сессии улучшены существенно: вместо 15-минутного timeout получен draft и полноценный semantic verdict примерно за 72 секунды. Но цель ещё не достигнута полностью: reviewer отклонил 2/4 obligations из-за upstream test-design setup. Оптимизация transport успешна; следующий bottleneck — качество prepared design-plan и deterministic state-change preflight.

Масштабируемость на medium scope этот run не доказывает: scope намеренно мал.
