# Gate V3 Cross-Canary Report

| canary | gate v3 | findings | решение |
| --- | --- | ---: | --- |
| character V4 | `fail` | 12 | Новый immutable character rerun обязателен до rollout. |
| numeric V2 | `pass` | 0 | Повторный live не нужен. |
| conditional V1 | `fail` | 5 | Историческое доказательство blind spot. |
| conditional V2 | `pass` | 0 | Remediation подтверждена live. |

Gate применяется к каждому TC отдельно. Отсутствующий ref, ref в другом TC и отсутствующий `DICT-*` являются blocking findings. Gap-obligations без executable TC не блокируются.
