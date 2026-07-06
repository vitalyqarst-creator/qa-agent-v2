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
- [references/agent/controlled-traceability-update-workflow.md](references/agent/controlled-traceability-update-workflow.md) — safe workflow for generated `REQ-*` traceability updates.

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
