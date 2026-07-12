# Runtime Setup Profile

## Metadata

| field | value |
| --- | --- |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| runtime_reference | `user-provided-local-only` |
| application | `cff` / `Credit Factory Frontend` |
| account_reference | `local-secret-not-published` |
| fixture_alias | `LOCAL-RESTRICTED-FIXTURE-01` |
| fixture_status | `Черновик` |
| data_policy | `read-only-ui-path` |
| publication_status | `safe-metadata-only` |

Runtime URL, login, password, session tokens, application identifier и персональные данные в артефакте не сохраняются.

## Setup Path

1. Открыть runtime URL из защищенной локальной конфигурации.
2. Авторизоваться согласованной тестовой учетной записью из локального secret storage.
3. В окне `Запуск приложения` выбрать `cff` и нажать `ЗАПУСТИТЬ`.
4. В таблице `Заявки` выбрать локальную fixture `LOCAL-RESTRICTED-FIXTURE-01` по непубликуемому идентификатору.
5. Нажать внутренний control кнопки `ПРОДОЛЖИТЬ`.
6. Убедиться, что открыта карточка выбранной fixture.

## Observed Fixture State

- summary area содержит пять видимых непустых label/value позиций, перечисленных в `BSR 44`;
- данные карточки не изменялись и не сохранялись.

## Limitations

- Путь создания или сброса этой fixture не предоставлен.
- Безопасный переносимый идентификатор fixture отсутствует; downstream setup остается заблокированным.
- Ни summary click, ни кнопка `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` в списке заявок не открыли calculator stage/window во время прогона `2026-07-12`.
- Профиль не снимает и не сужает `GAP-001`: полный состав prefill и exact mapping остаются неизвестными без внешнего ФТ `Калькулятор`.
