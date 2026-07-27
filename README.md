# FT Test Case Agent

Source-first агент для подготовки трассируемых тест-кейсов по DOCX с
обязательным XHTML-представлением и опциональной PDF-сверкой.

## Production runtime

Публичный runtime намеренно решает одну задачу: получает уже независимо
квалифицированный и hash-bound пакет выбранного scope, строит source-bound seed
cases, вызывает model writer в режиме `model-runtime-prose` только для runtime
prose, затем прогоняет deterministic gates и отправляет результат ровно одному
независимому reviewer. Bridge, benchmark, sharding, внутренние retry, hard model
timeout и запись в canonical здесь отсутствуют.

```powershell
ft-agent run `
  --config fts/<ft-slug>/work/<handoff>/run-config.json `
  --output-dir fts/<ft-slug>/work/iterations/<new-attempt-id>
```

Config schema v2 содержит базовые поля `schema_version`, `registry`, `ft_root`,
`scope`, `source_evidence` и `obligations`. Для актуального production route
добавляй `writer_mode: model-runtime-prose`. Output directory обязан быть новым.
Runner повторно проверяет registry boundary, source hashes, accepted source
receipt, obligations и текущий canonical baseline; source и canonical никогда не
изменяются.

Успешные terminal statuses:

- `accepted-shadow` — весь набор исполним;
- `accepted-with-calibration-pending` — reviewer принял исполнимую часть, а UI-
  calibration candidates явно оставлены pending; promotion запрещён.

После успешного запуска актуальный результат для просмотра указан в
`terminal-summary.json` → `publication_candidate.path`. Это shadow-файл текущего
run; `test-cases/*.md` не перезаписывается внутри `ft-agent run`.

Полный runtime-контракт: [lean-v2-iteration.md](references/agent/lean-v2-iteration.md).

## Честная граница bundle

Production bundle не является полным маршрутом «raw FT + название scope →
тест-кейсы». Discovery ФТ, выбор scope, extraction, source qualification и
independent source review пока выполняются в полной development/qualification
среде. Bundle начинается только с принятого prepared package. Это сознательная
граница, а не скрытая автоматизация.

Instruction context runtime задан файлами
[production-instruction-loading.md](references/agent/production-instruction-loading.md)
и [production-global-rules.md](references/agent/production-global-rules.md).

## Установка и проверка

```powershell
uv sync --no-dev
python scripts/probe_environment.py
ft-agent --help
python scripts/resolve_instruction_context.py `
  --manifest references/agent/production-instruction-loading.md `
  --scenario iteration.deterministic_production `
  --fail-on-budget
```

Production installation экспортирует только команду `ft-agent run`. Актуальный
маршрут для новых запусков — `model-runtime-prose`; legacy compatibility routes
не являются production-default. Tests, benchmarks, реальные FT inputs,
work/history, UI automation и qualification controllers в bundle не входят.

Сборка профилей описана в [release/README.md](release/README.md).

## Development repository

Полная рабочая копия дополнительно содержит `AGENTS.md`, `skills/`,
`references/`, qualification scripts, тесты и локальные FT-пакеты в `fts/`.
Они нужны для подготовки accepted source package, архитектурных проверок и
регрессий, но не загружаются production runtime.

Release-регрессия в полной development-среде запускается командой
`python -m unittest tests.test_release_bundle`.

Канонический полный запуск и быстрый agent-layer профиль:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py
.\.venv\Scripts\python.exe scripts/run_tests.py --suite agent-layer-fast
.\.venv\Scripts\python.exe scripts/run_tests.py --suite artifact-validator-sharded
```

Raw `unittest discover` не является каноническим полным запуском; команда
`.\.venv\Scripts\python.exe -m unittest discover -s tests` приведена только для
диагностики controlled-discovery расхождений.
