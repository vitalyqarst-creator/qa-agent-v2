# Архитектурная инвентаризация prepared pipeline

## Baseline

- Ветка до изменений: `audit/application-card-personal-data-iteration`, commit `5f1ed680b86af98644971fd0078ed5313a0392ed`.
- Script-first audit: 7 skills, 61 check, 0 findings, 0 stale items.
- Канонические границы уже существовали: prepared package, `stage-input.json`, отдельные exec sessions и runner-owned gates.
- Поэтому новая параллельная orchestration не создавалась.

## Карта слоев

| слой | канонический вход | выход | baseline finding | решение |
| --- | --- | --- | --- | --- |
| source/scope | DOCX/XHTML/PDF и handoff | atomic ledger/obligations/gaps | вне текущего изменения | сохранить upstream ownership |
| compiler | workflow-state canonical artifacts | immutable package v5 | standard package объявлял workspace writer | standard package теперь read-only/zero-command by default |
| dispatcher | JSON config | backend selection + runner | budget drift находился после создания cycle paths | authoritative `--validate-only` preflight до selection write |
| writer | package + 17 instruction files | draft | V3: 204696 primary bytes, 24 commands | embedded profile, context rule card, JSON draft contract, 0 commands |
| deterministic gates | draft/package | reports | отсутствовали title/gap/calibration bundle | quality bundle + calibration lifecycle |
| reviewer | draft/package + 19 instruction files | verdict | V3: 326387 primary bytes, 50 commands | embedded reviewer profile + gate summaries, read-only compact path |
| handoff | cycle artifacts | next stage | метрики были stage-level | context/coverage efficiency metrics |

## Duplication map

- `AGENTS.md`, skill map, full writer/reviewer skills, workflow/session formats повторно передавались стадиям, хотя scope/compiler уже применили эти правила.
- Package artifacts одновременно передавались как файлы и полностью встраивались в prompt.
- Writer/reviewer повторно запускали instruction resolver и читали перечисленные файлы.
- Reviewer повторял часть structure/traceability проверок, уже доступных runner-у.

## Целевая граница

- Prepared package и `stage-input.json` остаются источниками истины.
- `artifact-graph.json` — derived digest-bound lifecycle view, не новый источник требований.
- Structured writer/reviewer используют только embedded payload и runtime profile.
- Assisted mode — новый явный immutable cycle, не fallback внутри attempt.
- LLM выполняет test design и semantic review; filesystem navigation, Markdown structure, traceability completeness, duplicates и GAP markers проверяет runner.
