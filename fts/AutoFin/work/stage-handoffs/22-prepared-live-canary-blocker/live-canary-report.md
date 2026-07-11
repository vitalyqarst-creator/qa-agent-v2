# Live Canary Report: prepared widget selection

## Итог

- Статус: `blocked-input`.
- Promotion: выключен; production test cases не создавались и не изменялись.
- Standard-path control: не запускался после срабатывания стоп-условия.
- Блокирующий класс: false positive в `prepared-evidence-access-gate-v1` при чтении writer-ом собственного stage output.

## Границы прогона

- FT package: `fts/AutoFin`.
- Source family: `FT4AutoFinFinal.docx/xhtml/pdf`.
- Fast-path scope: `iteration-smoke-widget-selection-types`.
- Prepared package: `autofin-widget-selection-expanded-v2`, package version `4`, profile `simple-field-property`.
- Cycle: `work/review-cycles/codex-exec-prepared-widget-selection-live-v10-20260711`.
- CLI: локальный `codex exec` `0.144.0-alpha.4`; capability contract проверен через `exec --help`.

## Наблюдаемый результат

Writer стартовал в свежей ephemeral session `019f4f70-bc6b-7851-949d-afb0a6dce31f`, выполнил обязательный environment probe и создал unsigned draft в attempt root. Draft содержит 3 `TC-*`, имеет размер 6359 bytes и не содержит seed sentinel.

После создания draft writer прочитал только собственный файл:

`work/review-cycles/codex-exec-prepared-widget-selection-live-v10-20260711/attempts/writer-r1/attempt-001/stage-output/draft.md`

Gate классифицировал это как доступ к запрещенному корню `fts/AutoFin/work/review-cycles`, потому что проверяет простое вхождение forbidden-root в команду и не исключает runner-owned attempt root. Reviewer не стартовал.

## Почему это реальный blocker

- `stage-instructions.md` требует хранить output внутри attempt root.
- Writer имеет право проверить только что созданный stage-owned output.
- Prepared package запрещает старые cycle artifacts как requirement evidence, но текущий attempt root не является внешним evidence.
- Текущая реализация не различает эти случаи и поэтому делает корректную локальную self-check команду блокирующей.

## Safety checks

- `--promote-final` и `--promotion-dry-run` не передавались.
- Intended canonical path `test-cases/3-iteration-smoke-widget-selection-types.md` отсутствовал до запуска и не создан запуском.
- `git status -- fts/AutoFin/test-cases` показывает только ранее существовавший unrelated untracked файл `4.3-application-card-client-addresses-contacts.md`.
- Standard control и recovery/replay не запускались после blocker, чтобы сохранить причинность эксперимента.

## Рекомендуемое исправление

Перед следующим live canary gate должен принимать явный allowlist текущего attempt root и разрешать команды чтения внутри `attempts/<stage>/<attempt>/stage-output`, не ослабляя запрет на соседние/исторические `work/review-cycles/**`. Нужен regression test: own-output read passes, sibling-cycle read remains blocked.

