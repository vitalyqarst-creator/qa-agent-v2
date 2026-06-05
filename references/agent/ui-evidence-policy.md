# UI Evidence Policy

Этот reference фиксирует, какие UI-наблюдения могут подтверждать automation-ready статус тест-кейса, а какие должны оставаться ограничением, blocker или вспомогательным наблюдением.

## Назначение

- не позволять UI evidence подменять FT-first baseline;
- отделить нормальный пользовательский UI path от DOM-seeded и других synthetic observations;
- явно фиксировать переносимость evidence из `output/`;
- связать evidence quality с допустимыми `ui_verification_status`.

## Evidence Trust Levels

### Normal UI Path

Normal UI path означает, что кейс воспроизведен через обычный пользовательский flow:

- runtime URL открыт без скрытой подмены состояния;
- пользовательские действия выполнялись через UI;
- проверяемый результат наблюдался в интерфейсе или в допустимом пользовательском ответе системы;
- evidence содержит screenshot для `confirmed` или `mismatch-ft-ui`;
- trace сохранен для mismatch, unexpected navigation, падения шага или другого спорного результата.

Только normal UI path может быть основанием для:

- `confirmed`;
- `mismatch-ft-ui`.

### Local Output Evidence

Пути вида:

```text
output/playwright/<scope-slug>/...
```

являются локальными Playwright artifacts.

Они допустимы как evidence index, но не являются переносимыми в чистый checkout, если не экспортированы отдельно. Если такие пути используются, `ui-evidence-index.md` должен объявлять:

```md
- `evidence_export_policy`: `local-output-index-only`
- `artifact_availability`: пути `output/` являются локальными Playwright-артефактами и не переносимы в чистый checkout.
```

Local-only evidence не запрещает `confirmed`, но снижает воспроизводимость handoff. Для внешней передачи нужно экспортировать durable artifacts или явно оставить portability limitation.

### DOM-Seeded Observation

DOM-seeded observation означает, что агент получил состояние через инъекцию DOM, прямую подстановку данных, обход normal UI path или другой synthetic route.

DOM-seeded observation не может быть самостоятельным основанием для:

- `confirmed`;
- `mismatch-ft-ui`.

Если normal UI path не воспроизведен, используй один из статусов:

- `blocked-observability`;
- `blocked-access`;
- `blocked-ui-unavailable`;
- `not-automatable-manual-only`.

Если DOM-seeded observations все же индексируются, `ui-evidence-index.md` должен объявлять:

```md
- `dom_seeded_policy`: `non-canonical-observation`
- `downstream_rule`: `dom-seeded-not-confirmed`
```

## Trace Policy

Для `confirmed` обязателен screenshot.

Для `mismatch-ft-ui`, unexpected navigation, падения шага или спорного результата обязателен trace, если Playwright технически доступен.

Если traces намеренно не собирались, `ui-evidence-index.md` должен объявлять:

```md
- `trace_policy`: `not-collected`
```

и `ui-validation-report.md` должен явно фиксировать limitation. Отсутствие trace не должно маскироваться как полностью воспроизводимое evidence.

## Status Gate

Перед сменой `ui_verification_status` проверь:

| Status | Required evidence | Forbidden basis |
| --- | --- | --- |
| `confirmed` | normal UI path + screenshot | DOM-seeded only, user comment only, old screenshot only |
| `mismatch-ft-ui` | normal UI path + screenshot + trace when available | DOM-seeded only, assumption about UI behavior |
| `blocked-ui-unavailable` | failed runtime availability evidence or access log | guessed UI behavior |
| `blocked-access` | access failure evidence | bypassing auth without approval |
| `blocked-observability` | explanation why FT assertion is not observable in UI | invented UI reaction |
| `not-automatable-manual-only` | manual-only reason | deleting the case from automation-ready |

User comments after a run are input for rerun, not evidence for direct status change.

## Required Declarations In UI Evidence Index

Если применимо, `ui-evidence-index.md` должен содержать policy block before evidence table:

```md
## Evidence Policy

- `evidence_export_policy`: `local-output-index-only`
- `artifact_availability`: пути `output/` являются локальными Playwright-артефактами и не переносимы в чистый checkout.
- `dom_seeded_policy`: `non-canonical-observation`
- `trace_policy`: `not-collected`
- `downstream_rule`: `dom-seeded-not-confirmed`
```

Не добавляй policy declaration, если соответствующего ограничения нет. Ложная декларация хуже отсутствующей: она скрывает качество evidence.

## Relationship To Automation-Ready

Automation-ready case может уточнять executable flow только по фактически проверенному UI behavior.

Если evidence limited:

- сохраняй case в automation-ready;
- фиксируй blocker или limitation;
- не переписывай expected result под предположение;
- не меняй FT смысл без `FT/UI Divergence`.

