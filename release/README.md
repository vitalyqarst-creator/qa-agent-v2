# Release Profiles

Проект использует один исходный commit и два детерминированных профиля сборки.

## Qualification

`qualification-manifest.json` включает runtime, инструкции, тесты и curated
benchmark configs. Сырые прогоны, diagnostics, stage/review work и оригинальные
AutoFin DOCX/XHTML/PDF/mockups исключены. Активный `PostFinal-v2` и используемые
макеты связаны с профилем только путями и SHA-256; сами файлы остаются локальными.
Небольшие воспроизводимые DaData-fixtures входят в qualification-профиль.
Проверка локальных входов выполняется с `--require-local-inputs`.
Для запуска offline quality proof используй обычную репозиторную dev-среду после
`uv sync`; production installation может исключить dev group.

```powershell
python scripts/build_release_bundle.py `
  --manifest release/qualification-manifest.json `
  --check-only `
  --require-local-inputs
```

## Production

`production-manifest.json` — точный allowlist import closure для публичного
`ft-agent run`. Это намеренно узкий downstream runtime: он принимает уже
независимо принятый, hash-bound source package и выполняет только
детерминированную schema-v2 iteration с одним reviewer. Discovery исходного ФТ,
выбор scope, построение source evidence и independent source review в bundle не
входят. Эти prerequisite-этапы пока остаются в qualification/development среде.

В bundle входит только `ft-test-case-iteration`, его компактные runtime
references, environment probe и instruction resolver. Единственный instruction
entrypoint — `references/agent/production-instruction-loading.md`; он загружает
самодостаточную `production-global-rules.md`, поэтому development-only корневой
`AGENTS.md` и legacy control plane в production не копируются.

Профиль не содержит `evals/`, tests, FT inputs, work/history, benchmarks,
overnight/incremental/standard controllers, dispatcher/cycle-state compatibility,
UI automation, source qualification skills, legacy writer/reviewer skills и offline quality proof. Эти
инструменты остаются только в qualification-профиле. Публичный production CLI
содержит только `ft-agent run`.

```powershell
python scripts/build_release_bundle.py `
  --manifest release/production-manifest.json `
  --output dist/ft-test-case-agent-production
```

Output directory обязан быть новым. В корне bundle создаётся
`release-manifest.json` с SHA-256 каждого файла и общим `tree_sha256`.

Benchmark profile не превращается в отдельную кодовую ветку. Production bundle
строится из того же commit/tag, поэтому исправления runtime и quality gates не
расходятся между qualification и production.
