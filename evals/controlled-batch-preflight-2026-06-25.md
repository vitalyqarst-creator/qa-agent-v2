# Controlled Batch Preflight

## Цель

Подготовить следующий controlled batch для проверки качества тест-кейсов после последних улучшений agent-layer: тест-кейсы должны быть трассируемыми к функциональным требованиям, понятными и проходимыми.

## Выполнено

1. Проверены существующие signed-off/canary scope-ы через `codex_review_cycle_runner.py validate`.
2. Нормализован source-locator boundary в `fts/ft-2-OF_17/work/stage-handoffs/00-source-selection/`: активный package boundary исправлен с `ft-2-OF_16` на `ft-2-OF_17`.
3. Зафиксировано, что временный Word lock-файл из соседнего `fts/ft-2-OF_16/source/` не является source-документом и не должен попадать в downstream scope.
4. Из DOCX `fts/ft-2-OF_17/source/ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.docx` извлечена структура разделов-кандидатов.

## Gate Results

| artifact / scope | command | result | вывод |
| --- | --- | --- | --- |
| `history-editing-fresh-canary-v2` | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\history-editing-fresh-canary-v2\cycle-state.yaml` | pass | `valid=true`, `scoped_findings_count=0`, blockers `0` |
| `application-card-common-actions-flow-canary-v2` | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\application-card-common-actions-flow-canary-v2\cycle-state.yaml` | pass | `valid=true`, `scoped_findings_count=0`, blockers `0` |
| `document-print-form-tags-fresh-canary-v2` | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\document-print-form-tags-fresh-canary-v2\cycle-state.yaml` | pass with non-blocking findings | `valid=true`, `scoped_findings_count=2`, blockers `0` |
| `application-card-common-actions` baseline | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\application-card-common-actions\cycle-state.yaml` | fail | terminal signed-off имеет 19 unwaived current-scope findings; первый `split-artifact-redundant-section-heading` |
| full `fts/ft-2-OF_17` root validator | `python scripts\validate_agent_artifacts.py --root fts\ft-2-OF_17 --json --fail-on warning --session-log-policy audit --decision-log-policy strict` | fail | root содержит исторические/архивные findings: 3718 всего, 16 errors; это не годится как batch gate |

## Candidate Ranking

| rank | candidate | decision | rationale |
| --- | --- | --- | --- |
| 1 | Узкий scope `client-documents-upload-and-actuality` внутри `Раздел «Анкета клиента» / «Обработка»` | recommended | Есть проверяемые UI-поля/виджеты и действия: загрузка документов, актуальность документа, ограничения форматов `jpeg/png/pdf` и размера `30 МБ`, действия `Актуальный`, `Неактуальный`, `Отправить СМС на подписание документов онлайн`, `Назад`, `Отправить заявку`. Scope нужно ограничить только document upload/actuality behavior, без всей анкеты и без полного тегового шаблона печатных форм. |
| 2 | `Раздел «Предложения»` | reject for this batch | В DOCX найден только макет без таблицы требований; агенту пришлось бы выводить поведение из изображения, что противоречит цели FT-first тест-кейсов. |
| 3 | Весь `Раздел «Анкета клиента» / «Обработка»` | reject as too broad | Раздел включает большую таблицу полей, действия, печатные формы и таблицу тегов на 49 строк. Это приведет к крупному scope-у и затруднит диагностику качества агента. |
| 4 | Старый `ui-employment` | reject for clean batch | Исторический cycle имеет `ft_slug=ft-2-OF_16`, `round-cap-reached` и много старых quality smells; использовать его как новый clean signal нельзя. |

## Recommended Next Execution

1. Создать новый handoff `fts/ft-2-OF_17/work/stage-handoffs/08-client-documents-upload-and-actuality/`.
2. В scope включить только source-backed утверждения про:
   - видимость информационных сообщений по приложенным/подписанным документам;
   - разрешенные форматы `jpeg`, `png`, `pdf`;
   - ограничение размера `30 МБ`;
   - отображение миниатюр/имени/размера/формата загруженных файлов;
   - условия актуальности/неактуальности документа;
   - действия `Актуальный`, `Неактуальный`, `Отправить СМС на подписание документов онлайн`, `Назад`, `Отправить заявку`.
3. Явно вынести в out-of-scope:
   - полный теговый шаблон заявления-анкеты;
   - полную интеграционную цепочку СМС-шлюза, ППК, ЭА, СПР, ПДН/МПЛ;
   - backend/API/RabbitMQ/БД эффекты без UI-наблюдаемого результата;
   - весь соседний `Предложения`.
4. После создания scope artifacts запускать только scoped review-cycle validate; full root validator использовать как backlog signal, а не как blocking gate.

## Blocking Notes

- Перед новым запуском нельзя использовать root-level validator как обязательный gate для всего `ft-2-OF_17`: исторические `versions/` и старые `ui-employment` артефакты дают нерелевантные ошибки.
- Старый baseline `application-card-common-actions` нельзя считать качественным signed-off без remediation: terminal gate его не пропускает.
- Новый batch должен сравниваться с прошедшими canary scope-ами (`history-editing-fresh-canary-v2`, `application-card-common-actions-flow-canary-v2`) и с manual sampling scorecard, а не со всем историческим деревом.
