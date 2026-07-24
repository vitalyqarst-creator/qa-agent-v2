---
name: ft-test-case-iteration
description: Run one source-qualified test-case iteration for an already selected FT package and confirmed scope through the public `ft-agent run` command.
---

# FT Test Case Iteration

Используй этот skill только после выбора FT-пакета и подтверждения внешнего
scope. Production-профиль имеет один публичный entrypoint: schema-v2 config →
свежий immutable attempt → source-bound writer route → deterministic gates →
ровно один независимый reviewer → `accepted-shadow`, честный
`accepted-with-calibration-pending` либо явная terminal failure.

## Входы

До запуска должны существовать:

- package-local `scope-registry.json` с выбранным scope, стабильным `tc_prefix`,
  структурной XHTML-границей и полным реестром DOCX/XHTML/PDF/support/mockups;
- DOCX как source of truth и matching XHTML как обязательный extraction source;
- source evidence с manifest v4, independent accepted review receipt на точный
  digest и hash-bound semantic compiler projection;
- compiler-v3 obligations;
- package `AGENT-NOTES.md`, если он существует.

Новый `run-config.json` использует schema v2. Базовые обязательные поля:

```json
{
  "schema_version": 2,
  "registry": "fts/example-ft/scope-registry.json",
  "ft_root": "fts/example-ft",
  "scope": "confirmed-scope",
  "source_evidence": "fts/example-ft/work/handoff-001/source-evidence.md",
  "obligations": "fts/example-ft/work/handoff-001/obligations.json"
}
```

Для новых production попыток добавляй `writer_mode: model-runtime-prose`.
Допустимые route-поля: `writer_mode`, `mockup_label_aliases`,
`revision_findings`. Если `writer_mode` отсутствует, runner использует
compatibility default `deterministic-first`. Не добавляй `ft_slug`, design
context, готовые derivations, `tc_prefix`, source/canonical allowlists, model
responses, publication target или lifecycle status. Runner выводит slug и
context из принятых контрактов, а derivations строит сам.

Если вход отсутствует, stale, неоднозначен или не hash-bound, не обходи
проверку: верни задачу в `ft-source-locator` / `ft-scope-analyzer` либо заверши
scope как `blocked-input`.

## Workflow

1. Прочитай package `AGENT-NOTES.md`, если он есть, и проверь, что выбранные
   `ft_root` и `scope` совпадают с запросом пользователя.
2. Выбери новый каталог attempt внутри `fts/<ft-slug>/work/`. Каталог не должен
   существовать. Не используй результаты прошлой попытки как model input.
3. Запусти единственную публичную команду:

```powershell
ft-agent run `
  --config fts/<ft-slug>/work/<handoff>/run-config.json `
  --output-dir fts/<ft-slug>/work/iterations/<new-attempt-id>
```

4. Не выполняй параллельно ручное написание или review. Runner сам компилирует
   source set, строит graph/context/seed cases, в `model-runtime-prose` один раз
   вызывает writer только для runtime prose, затем выполняет gates, собирает
   `ReviewerEvidencePack` v2, передаёт draft ровно одному независимому reviewer
   и повторно проверяет run/source/canonical hashes.
5. Считай успехом `accepted-shadow` либо
   `accepted-with-calibration-pending` с реальным reviewer receipt и закрытыми
   gates. Во втором случае calibration-кандидаты имеют reviewer status
   `calibration-pending`, а весь набор явно не допускается к promotion. Это не
   publication: canonical и workflow state не меняются.
6. При terminal failure сохрани diagnostic как результат attempt. Исправление
   выполняй отдельно; повтор запускай только в новом каталоге.

## Выходы

Один immutable attempt содержит scope/contract bindings, generated derivations,
coverage graph, bound context, shadow Markdown, production gate, full
`reviewer-evidence-basis.json`, hash-bound `reviewer-evidence-pack.json`,
writer/reviewer receipts по фактически использованному route и terminal summary
с phase time, attempts, artifact sizes и token metrics.

Допустимые успешные статусы — `accepted-shadow` и
`accepted-with-calibration-pending`; последний всегда содержит
`promotion_eligible=false` и `non_promotable_reason=calibration-pending`.
Blocking contract/input/design, review findings и infrastructure failure
остаются честными terminal outcomes.

Если terminal findings передаются в отдельный remediation cycle, handoff
сохраняет `affected_traceability_refs`; закрытие traceability gaps проверяется по `traceability_ref` / `atom_id`.
Такой handoff сохраняется в `stage-handoffs/`, а его единственным process-status
остается `workflow-state.yaml`; не изменяй его внутри текущего immutable
production attempt.

После отдельного signed-off handoff дальнейшая проверка в реальном UI — это
post-iteration вход в `ft-ui-automation-prep` с выпуском отдельной
automation-ready версии; не запускай этот skill внутри текущего immutable
production attempt.

## Out-of-profile

Incremental FT-version updates, benchmarks, UI automation и историческая
session/cycle orchestration не входят в этот production profile. Для них нужна
отдельная qualification/development среда; не подмешивай их процедуры,
артефакты или fallback-маршруты в текущий attempt.

## Канонические references

- Production instruction context: [../../references/agent/production-instruction-loading.md](../../references/agent/production-instruction-loading.md)
- Production global rules: [../../references/agent/production-global-rules.md](../../references/agent/production-global-rules.md)
- Source-qualified iteration contract: [../../references/agent/lean-v2-iteration.md](../../references/agent/lean-v2-iteration.md)
- UI calibration candidates: [../../references/agent/negative-ui-calibration-policy.md](../../references/agent/negative-ui-calibration-policy.md)

## Ограничения

- Не выполняй discovery FT-пакета или первичный выбор scope внутри этого skill.
- Не передавай reviewer старые test cases, benchmark/history или произвольные
  незарегистрированные файлы.
- Не задавай hard model timeout и не делай внутренний retry.
- Не редактируй canonical, source files или workflow state.
- Не выдавай offline/precomputed acceptance за реальный reviewer result.
