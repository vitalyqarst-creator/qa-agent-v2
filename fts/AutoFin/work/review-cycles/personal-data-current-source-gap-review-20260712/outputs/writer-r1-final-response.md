Выполнил `writer-r1` rebuild по current source.

Draft и артефакты:
- Draft: [writer-r1-draft.md](</C:/Users/Пользователь/Documents/Виталя/GitProjects/qa-agent-v2/fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md>)
- Split design: [14-application-card-client-personal-data](</C:/Users/Пользователь/Documents/Виталя/GitProjects/qa-agent-v2/fts/AutoFin/work/test-design/14-application-card-client-personal-data>)
- Block report: [writer-r1-blocked-input.md](</C:/Users/Пользователь/Documents/Виталя/GitProjects/qa-agent-v2/fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-blocked-input.md>)
- Cycle state: [cycle-state.yaml](</C:/Users/Пользователь/Documents/Виталя/GitProjects/qa-agent-v2/fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/cycle-state.yaml>)

Что сделано:
- Перестроены artifacts по FT4/XHTML rows и `BSR 47`..`BSR 77`.
- Покрыты `11/11` source rows, `42/42` atoms, `20/20` calibration obligations.
- `SO-NEG-001`..`SO-NEG-015` и `SO-REQ-001`..`SO-REQ-005` материализованы как отдельные candidate TC.
- Production canonical `test-cases/14-application-card-client-personal-data.md` не изменял.

Статус: `blocked-input`, не `writer-draft-ready`.

Причина: writer-owned draft/test-design scoped filter чистый (`0` warning/error), но runner `validate` включает старый production canonical file в current-scope gate и находит 22 warning/error findings. Writer-r1 по контракту не имеет права обновлять canonical до reviewer sign-off, поэтому я не стал маскировать это как ready.

Проверка:
- `python scripts/codex_review_cycle_runner.py validate --state .../cycle-state.yaml` теперь проходит: `valid: true`, next action `none` для `blocked-input`.