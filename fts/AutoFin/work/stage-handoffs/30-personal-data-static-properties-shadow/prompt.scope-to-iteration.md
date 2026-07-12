# Следующая prepared-итерация: ограничения символов ФИО

## Цель этапа

Проверить prepared-standard маршрут на небольшом реальном scope `BSR 48`, `BSR 51`, `BSR 54`: допустимые и недопустимые символы для полей `Фамилия`, `Имя`, `Отчество` без DaData и без изменения production baseline.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/workflow-state.yaml`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/iteration-summary.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/iteration-session-log.md`;
- `work/review-cycles/personal-data-static-properties-shadow-v6-20260712/cycle-state.yaml`.

## Обязательные действия

1. Создать новую eval-only compiler projection только для `BSR 48`, `BSR 51`, `BSR 54` и связанных non-blocking UI-calibration gaps.
2. Задать concrete fixtures для допустимого текста, дефиса и каждого отдельно проверяемого недопустимого класса до compiler/live exec.
3. Позволить compiler самостоятельно выбрать `standard-required`; не переопределять route вручную.
4. Запустить новый immutable cycle через `codex exec` без SDK fallback, promotion и production write.
5. Проверить atomicity, semantic overlap, coverage/gap preservation, time и token metrics.

## Не делать

- Не включать DaData `BSR 49`, `BSR 52`, `BSR 55`.
- Не выдумывать точный текст ошибки, подсветку, filtering или save-blocking, отсутствующие в источнике.
- Не использовать production/старые test cases как requirement evidence.
- Не изменять `test-cases/14-application-card-client-personal-data.md`.

## Ожидаемые выходы

- новый compiler input и immutable prepared-standard package;
- writer/reviewer cycle artifacts и semantic-overlap diagnostic;
- draft с source-backed позитивными проверками и явно сохранёнными calibration gaps;
- performance report, session/decision logs и обновлённый workflow state.

## Gate завершения

Этап завершён, когда compiler выбрал корректный route, все obligations покрыты либо сохранены как точные gaps, reviewer вынес доказуемый verdict, production baseline не изменён, а метрики сопоставлены с V6 без смешивания scope-классов.
