# FT Test Case Agent

Source-first агент для подготовки трассируемых тест-кейсов по DOCX с
обязательным XHTML-представлением и опциональной PDF-сверкой.

## Рабочий маршрут

Для нового scope используй [practical route v0.9](references/agent/practical-test-case-route-v0.9.md)
и skill `ft-practical-route`. Маршрут ведёт от выбранного scope до принятого
FT-first baseline либо честного внешнего blocker-а:

1. source manifest, `scope-obligations.json` и всегда создаваемый
   `scope-clarification-requests.md`;
2. русскоязычная matrix и независимое matrix review в отдельной Codex-сессии;
3. canonical test cases и независимое final TC review в отдельной Codex-сессии;
4. не более одной содержательной revision и одного fresh re-review в каждой
   из двух фаз.

`benchmark`, `sharding`, source-qualified runtime, session-based review-cycle
и другие исторические execution routes не входят в активный маршрут. Они
сохранены только как архив и не должны выбираться для новых прогонов.

После принятого baseline можно использовать `ft-ui-automation-prep`: UI
уточняет воспроизводимость и выпускает отдельную automation-ready версию, не
перезаписывая FT-first baseline.

## Установка и проверка

```powershell
uv sync --no-dev
python scripts/probe_environment.py
python scripts/resolve_instruction_context.py `
  --scenario practical.v0_9 `
  --fail-on-budget
```

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
