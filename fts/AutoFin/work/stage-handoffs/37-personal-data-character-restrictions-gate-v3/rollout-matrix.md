# Rollout Matrix

| profile | immutable canary | gate v3 | quality | reviewer | rollout result |
| --- | --- | --- | --- | --- | --- |
| `character-restriction-calibration` | character V5 | `pass`, 12/12, 0 findings | `pass` | `accepted`, 0 blocking findings | `pass` |
| `numeric-boundary` | numeric V2 | `pass`, 0 findings | `pass` | `accepted` | `pass` |
| `conditional-state` | conditional V2 | `pass`, 5/5, 0 findings | `pass` | `accepted`, 0 blocking findings | `pass` |

Итог: `controlled-rollout-ready`.

Это решение разрешает следующий ограниченный eval-run structured prepared pipeline. Оно не разрешает promotion, overwrite или изменение FT-first baseline без отдельного production contract.

## Character V4 -> V5

| metric | V4 | V5 | изменение |
| --- | ---: | ---: | ---: |
| gate v3 findings | 12 | 0 | -12 |
| duration, ms | 84469 | 94657 | +12.1% |
| total tokens | 56267 | 57043 | +1.4% |
| uncached input tokens | 52374 | 52755 | +0.7% |
| primary context bytes | 95302 | 97222 | +2.0% |
| commands / file changes | 0 / 0 | 0 / 0 | без изменения |

Рост времени не является блокером: token/context drift мал, quality и traceability исправлены. Повторный live-run ради усреднения в этой итерации запрещён правилом одного canary.
