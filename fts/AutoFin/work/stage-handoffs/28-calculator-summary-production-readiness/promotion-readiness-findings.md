# Promotion Readiness Findings

## Verdict

`v9 semantic candidate = accepted`, но `v9 production readiness = fail`.

Прямое копирование v9 в production запрещено. Нужен новый immutable canonicalization cycle; v8/v9 terminal state не replay.

## Findings

| finding_id | severity | category | evidence | required_change |
| --- | --- | --- | --- | --- |
| `PR-001` | `error` | `canonical-id` | v9 использует `TC-PREP-001..005`, production использует `TC-ACCS-*` | Выпустить ровно `TC-ACCS-001..005` в указанном порядке |
| `PR-002` | `error` | `package-id` | v9 использует runtime package id `autofin-prepared-standard-calculator-summary-final-v9` | Для Metadata и каждого TC использовать `WP-01` |
| `PR-003` | `error` | `canonical-structure` | v9 не содержит `Metadata`, `Scope Boundaries`, `Coverage Summary`, `Test Cases` | Восстановить все канонические разделы без изменения семантики обязательств |
| `PR-004` | `error` | `promotion-state` | статус v9 не отличает semantic acceptance от production readiness | Пропускать candidate к promotion только после отдельного machine gate |
| `PR-005` | `warning` | `semantic-preservation` | production содержит четыре TC, v9 — пять; BSR 46 разделён на opening и prefill | Сохранить отдельные `TC-ACCS-004` и `TC-ACCS-005`, не объединять их |
| `PR-006` | `error` | `metadata` | v11 удалил `test_design_dir` из Metadata | Сохранить `work/test-design/14-application-card-calculator-summary-entrypoints` |
| `PR-007` | `error` | `priority-format` | v11 заменил канонические `High/Medium` на `средний` | Использовать `High, High, Medium, High, Medium` для TC-001..005 |

## Frozen Semantic Mapping

| obligation | atom | req_id | accepted candidate | canonical output |
| --- | --- | --- | --- | --- |
| `OBL-001` | `ATOM-001` | `BSR 43` | `TC-PREP-001` | `TC-ACCS-001` |
| `OBL-002` | `ATOM-002` | `BSR 44` | `TC-PREP-002` | `TC-ACCS-002` |
| `OBL-003` | `ATOM-003` | `BSR 45` | `TC-PREP-003` | `TC-ACCS-003` |
| `OBL-004` | `ATOM-004` | `BSR 46` | `TC-PREP-004` | `TC-ACCS-004` |
| `OBL-005` | `ATOM-005` | `BSR 46` | `TC-PREP-005` | `TC-ACCS-005` |
| `OBL-006` | `ATOM-006` | `BSR 46` | `GAP-001` | `GAP-001` |

## Hash Lock

- Accepted v9 SHA-256: `7f7e076abf1faca3e4bf58e8aab62f2b7beec6ffd1e63ef4a05be4cc29c0bc00`.
- Production-before SHA-256: `a32a6049a5ca9f88d5c9e8d379bfd390724db688bc1d69c4b409e83743ac75f5`.
- Production-before git blob: `bdf46a84ecdb827774a25eb3b5753088a27866dd` at checkpoint `8f5233c`.
- Final XHTML SHA-256: `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66`.
- Final PDF SHA-256: `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58`.
- Final DOCX pinned SHA-256 from handoff 27: `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b`.

## Stop Conditions

- Любое изменение закреплённого v9 SHA.
- Потеря `GAP-001` или BSR 43–46.
- Появление BSR 35–38 в calculator-summary.
- Любое изменение соседнего production-файла.
- Semantic reviewer `changes-required` после одного разрешённого correction round.
