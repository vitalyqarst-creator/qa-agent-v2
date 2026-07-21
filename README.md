# FT Test Case Agent

Легкий Python-пакет для agent-first разбора функциональных требований из `.docx` и `.pdf`.

## Основные слои

В проекте есть три уровня:

- `AGENTS.md` — роль и общие правила работы QA-агента.
- `skills/` — workflow для поиска ФТ, выделения scope, написания и review тест-кейсов.
- `references/` — канонические форматы, QA-правила и agent-layer контракты.
- `test_case_agent/` — техническое ядро: чтение документов, выделение разделов и чанков.

FT-пакеты хранятся в `fts/`. В чистой export-версии эта папка может отсутствовать или быть пустой, но рабочая копия проекта может содержать реальные FT-пакеты и их артефакты. Новые рабочие материалы добавляются по FT-пакетам; каждый пакет хранится в своей папке:

```text
fts/
  <ft-slug>/
    source/            # основное ФТ: docx/pdf
    support/           # связанные документы, справочники, дополнительные материалы
    mockups/           # макеты экранов
    test-cases/        # тест-кейсы только по этому ФТ
    work/              # промежуточные артефакты, превью, заметки
    README.md          # краткая карточка конкретного FT-пакета
```

Для межэтапного handoff внутри `work/` используются две канонические зоны:

- `stage-handoffs/<scope-slug>/` — `workflow-state.yaml`, scope contract и prompt-файлы для следующего этапа;
- `review-loops/<scope-slug>/` — findings, traceability matrix, writer response, loop summary и snapshots.

Такая структура нужна для двух вещей:

- сразу видно, какие материалы относятся к конкретному ФТ;
- тест-кейсы не смешиваются между разными FT-пакетами.

Проект не использует обязательный CLI и не зависит от LLM-генерации как от основного режима работы. Основной путь использования — агентный workflow плюс Python API пакета `test_case_agent`.

## Быстрые ссылки

- [fts/README.md](fts/README.md) — индекс FT-пакетов, если `fts/` присутствует в рабочей копии.
- [references/agent/user-interaction-guide.md](references/agent/user-interaction-guide.md) — краткая инструкция для пользователя по эффективной работе с агентом.
- [references/agent/user-manual.md](references/agent/user-manual.md) — редактируемый источник полного пользовательского справочника; финальные версии генерируются в `output/doc/` и `output/pdf/`.
- [references/agent/instruction-contract-index.md](references/agent/instruction-contract-index.md) — карта канонических источников правил, потребителей и validator coverage.
- [references/agent/content-placement.md](references/agent/content-placement.md) — правила размещения знаний между `AGENTS.md`, `skills/`, `references/`, `fts/` и кодом.

## Что умеет пакет

- читать требования из DOCX и PDF;
- выделять разделы по иерархии документа;
- сужать выборку по нужному разделу;
- показывать превью больших scope через чанки;
- использовать PDF-версию ФТ для сверки структуры разделов, если она доступна в пакете;
- анализировать документы `.docx` и `.pdf` без внешней LLM-зависимости.

## Быстрый старт

1. Установить зависимости:

```powershell
uv sync
```

2. Использовать Python API на выбранном документе требований:

```python
from test_case_agent import load_sections, preview_chunks, resolve_sections

source = "fts/<ft-slug>/source/<requirements-file>.docx"

sections = resolve_sections(source, section_prefix="<section-prefix>")
chunks = preview_chunks(source, section_prefix="<section-prefix>", max_chars=12000)
all_sections = load_sections(source)
```

Практический сценарий: найти нужное ФТ, сузить scope, написать тест-кейсы отдельным skill-ом и сохранить их в папку пакета.
Для воспроизводимого pipeline между этапами используй `workflow-state.yaml` и handoff prompt-файлы из `work/stage-handoffs/<scope-slug>/`.

## Review-cycle runners

Каноническая точка запуска — `scripts/review_cycle_backend_dispatcher.py`. Режим `--backend auto` сначала проверяет локальный контракт `codex exec --help` и по умолчанию выбирает stage-per-process backend `scripts/codex_exec_review_cycle_runner.py`. Тихий откат запрещён: SDK разрешён только явно через `--backend sdk` либо через одновременно заданные `--backend auto --allow-sdk-fallback`. `scripts/codex_review_cycle_runner.py` сохраняется как диагностический fallback для v1 SDK/app-server contract, а не как default route. `--run-profile production` является рабочим default и сохраняет все quality gates без расширенного сканирования benchmark evidence; `--run-profile benchmark` требует `--performance-output` и добавляет детальную атрибуцию событий, context и времени.

Dispatcher принимает JSON-конфигурацию v1 с `exec_runner_args`, `sdk_runner_args` и `cycle_dir`, сам выполняет capability probe и добавляет проверенный CLI contract в exec runner. Каждый live-запуск требует нового cycle directory без runner-owned outputs. Writer interruption считается `completed-with-progress` только когда draft существует и проходит deterministic gates; частичный reviewer output никогда не принимается. После остальных прерываний создаётся новый immutable cycle, а prepared package перекомпилируется под его новый attempt — replay старого draft или resume старой LLM-сессии не выполняется. Повторное использование того же package output через `compile_prepared_stage_package.py --reuse-if-current` допускается только при полном совпадении v7 `input_fingerprint`; изменившийся source, compiler evidence, obligation contract или attempt binding требует нового immutable package id. Если help/auth/sandbox contract не подтверждён, `auto` останавливается как `blocked-exec-runtime`; final artifact не создаётся. Полные параметры доступны через `python scripts/review_cycle_backend_dispatcher.py --help` и `python scripts/codex_exec_review_cycle_runner.py --help`.

Для `simple-field-property` prepared-fast route по умолчанию использует `--prepared-fast-writer-mode structured`: writer работает в `read-only`, не вызывает команды и возвращает полный Markdown внутри JSON contract; draft атомарно создаёт и валидирует runner. `--prepared-fast-writer-mode workspace` остаётся только явным legacy fallback и никогда не включается автоматически после malformed output, timeout или validator failure.

Для `standard-required` действует тот же безопасный default через `--prepared-standard-writer-mode structured`: writer и reviewer получают bounded prepared context, writer имеет нулевой command budget, а runner создаёт draft, artifact graph, calibration lifecycle и deterministic gate bundle. `--prepared-standard-writer-mode assisted` разрешён только как явный новый immutable cycle для точечного source fallback.

## Release profiles

Стабильный qualification baseline содержит тесты и curated benchmark configs, но
не содержит сырые прогоны, diagnostics или оригинальные AutoFin sources/mockups.
Production bundle собирается из того же commit по отдельному allowlist и не
содержит `evals/`, `tests/`, `fts/` и work/history. Команды и точный contract:
[release/README.md](release/README.md).

## Как запускать тесты

Канонический способ запуска тестов в репозитории:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py
```

Скрипт запускает обычные test modules через controlled discovery, исключает монолитный `tests.test_agent_artifact_validator` и затем запускает его через sharded wrapper. Raw `unittest discover` не является каноническим full-run режимом, потому что он запускает artifact-validator монолитно:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Обычный `python -m unittest` в этом репозитории может не подхватить suite полностью.

Для быстрых проверок отдельных слоев:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py --suite agent-layer
.\.venv\Scripts\python.exe scripts/run_tests.py --suite agent-layer-fast
.\.venv\Scripts\python.exe scripts/run_tests.py --suite architecture
.\.venv\Scripts\python.exe scripts/run_tests.py --suite artifact-validator-sharded
```

`architecture` запускает governance-аудит `skills/`, `references/`, `AGENTS.md` и scripts через `agent-architecture-auditor` и падает на warning. Используй его перед изменениями агентных инструкций и после них.

`agent-layer-fast` запускает agent-layer тесты без тяжелого artifact-validator. `agent-layer` запускает fast agent-layer и затем `artifact-validator-sharded`.

`artifact-validator-sharded` запускает тяжелый `tests.test_agent_artifact_validator` полным покрытием через 7 shard-ов и является каноническим локальным режимом вместо длинного монолитного процесса. Для CI fan-out можно запускать отдельный shard: `.\.venv\Scripts\python.exe scripts/run_tests.py --suite artifact-validator --shard-count 7 --shard-index 1`.

## Публичный API

- `load_sections(source)` — получить разделы и метаданные по документу.
- `resolve_sections(source, section_prefix=None, max_sections=None)` — выбрать релевантные разделы.
- `preview_chunks(source, section_prefix=None, max_sections=None, max_chars=12000)` — показать чанки для большого фрагмента.
- `inspect_source_quality(source, max_chars=12000)` — получить диагностические предупреждения по качеству извлечения структуры и chunking.

Также экспортируются модели `Section`, `SectionChunk` и исключения `InvalidSourceError`, `NoMatchingSectionsError`.

## Где проект особенно полезен

1. Когда нужно быстро разобрать DOCX/PDF.
2. Когда нужно сузить анализ до конкретного раздела требований.
3. Когда один документ слишком большой для ручного просмотра целиком.
4. Когда агент должен опираться на структуру документа перед написанием тест-кейсов.

## Ограничения

- PDF извлекается как плоский текст и может хуже сохранять структуру;
- DOCX не всегда размечен идеально, поэтому заголовки и вложенность разделов могут требовать дополнительной проверки;
- если требования сформулированы неоднозначно, такие места лучше выносить в `coverage gaps`, а не додумывать.
