# Test Case Versioning Policy

Этот документ задает каноническое правило хранения текущих и промежуточных версий ручных тест-кейсов.

## Цель

Policy нужна, чтобы:

- сохранять один канонический текущий набор тест-кейсов;
- не терять состояние набора между writer/reviewer сессиями;
- обеспечивать трассируемость изменений по session-based review cycle;
- не плодить несколько конкурирующих основных версий одного и того же scope.

## Канонический Набор

Для каждого `scope-slug` должен существовать один текущий канонический набор:

```text
fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md
```

`<section-id>` - номер раздела ФТ, по которому выбран scope, например `2.1` или `2.2.2.1`.

Именно этот файл считается актуальным входом для:

- `ft-test-case-writer`;
- `ft-test-case-reviewer`;
- `ft-test-case-iteration`;
- `ft-ui-automation-prep`.

Не создавай в `test-cases/` файлы вида `<scope>-round-1.md`, `<scope>-draft.md`, `<scope>-signed-off.md` или другие конкурирующие основные версии.

## Snapshot-Версии

Промежуточные snapshot-версии не заменяют канонический набор.

Для новых session-based cycles snapshots сохраняются только здесь:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/versions/<snapshot-id>/
```

Snapshot - это полный слепок состояния на конкретной контрольной точке cycle. Он должен включать `snapshot-manifest.yaml` с путями, размерами и SHA-256 для скопированных файлов.

Новые прогоны не должны писать snapshots в `work/review-loops/`.

## Когда Snapshot Обязателен

Snapshot должен сохраняться:

- перед writer-сессией, если есть предыдущая версия canonical файла;
- после initial writer draft;
- после каждого writer-pass, который меняет canonical test-case file или split test-design artifacts;
- после reviewer-сессии, которая меняет routing/status evidence;
- после `signed-off`;
- после `round-cap-reached`;
- перед крупным пересмотром ранее согласованного набора, если иначе будет потеряно важное промежуточное состояние.

## Когда Snapshot Не Нужен

Отдельный snapshot не нужен:

- после мелких редакторских правок без изменения сути покрытия;
- после исправления опечаток, форматирования или локальных формулировок;
- если не было отдельной контрольной точки writer/reviewer cycle.

## Recommended Snapshot IDs

Используй стабильные id из `references/agent/session-based-review-cycle-format.md`, например:

- `r0-baseline`;
- `r1-writer-draft`;
- `r1-structure-preflight`;
- `r1-semantic-review`;
- `r2-writer-revision`;
- `r2-semantic-review`;
- `final-format-review`;
- `final-format-revision`;
- `final-semantic-regression`;
- `signed-off`;
- `round-cap-reached`.

## Связь С Другими Артефактами

Snapshot не заменяет:

- `cycle-state.yaml`;
- `codex-session-map.yaml`;
- reviewer findings;
- traceability matrices;
- writer response artifacts;
- final reviewer response или stage output summary.

Эти артефакты для новых cycles хранятся рядом в:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/
```

Рекомендуемая структура:

```text
fts/<ft-slug>/test-cases/
  <section-id>-<scope-slug>.md

fts/<ft-slug>/work/review-cycles/<scope-slug>/
  cycle-state.yaml
  codex-session-map.yaml
  prompts/
    prompt.writer-r1.md
    prompt.writer-to-reviewer.round-1.md
  outputs/
    structure-preflight-r1-final-response.md
    semantic-review-r1-final-response.md
    writer-r2-final-response.md
  versions/
    r0-baseline/
      snapshot-manifest.yaml
    r1-writer-draft/
      snapshot-manifest.yaml
    signed-off/
      snapshot-manifest.yaml
```

## Legacy Review-Loops

`fts/<ft-slug>/work/review-loops/<scope-slug>/` является legacy-only хранилищем исторических прогонов. Его можно читать при миграции, аудите или сравнении старого результата, но новый writer/reviewer процесс не должен создавать там новые prompt, findings, snapshots или summary.

Не удаляй legacy `review-loops` автоматически: там может лежать evidence уже выполненных прогонов и fixtures для обратной совместимости валидатора.

## Обязательные Правила

- Сначала обновляется канонический файл в `test-cases/`, затем runner сохраняет snapshot контрольной точки.
- `test-cases/` хранит только текущий baseline для scope, не историю.
- `work/review-cycles/<scope>/versions/` хранит историю.
- `cycle-state.yaml` является source of truth для session-based process status.
- `workflow-state.yaml` может ссылаться на `cycle-state.yaml` для совместимости, но не должен вести новый процесс обратно в `work/review-loops/`.
