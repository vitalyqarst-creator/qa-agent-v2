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
| controlled_rerun_gate_review | `2026-07-12` |
| controlled_rerun_gate_status | `blocked` |

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
- Documented create/select/reset path для synthetic fixture в remediation inputs не появился.
- Ни summary click, ни кнопка `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` в списке заявок не открыли calculator stage/window во время прогона `2026-07-12`.
- Новый подтвержденный normal UI entrypoint и product/FT-owner disposition по двум divergences отсутствуют; controlled rerun не запускался.
- Профиль не снимает и не сужает `GAP-001`: полный состав prefill и exact mapping остаются неизвестными без внешнего ФТ `Калькулятор`.
