# Regression eval: сложный scope должен иметь внутренние рабочие пакеты

## Цель

Этот eval проверяет, что агент не передает большой неоднородный scope writer-у как плоский список требований.

Правильное поведение:

- `ft-scope-analyzer` делает `Scope Complexity Assessment`;
- если scope неоднородный, он либо предлагает split на внешние scopes, либо создает `Внутренние Рабочие Пакеты`;
- `ft-test-case-writer` пишет ledger и `TC-*` package-by-package;
- `ft-test-case-reviewer` отклоняет набор, если writer смешал независимые проверки из разных packages.

## Входной Сценарий

Пользователь выбирает один внешний scope:

```text
ФТ 2, раздел 2.3 Основная информация.
Нужно написать тест-кейсы по всему разделу.
```

Фрагмент содержит:

- свойства полей формы;
- числовые, датовые и длиновые ограничения;
- условные зависимости;
- справочники и DaData;
- действия `Следующий шаг`, `Назад`, `Редактировать`;
- интеграционные действия `Проверить` и `Отправить повторно`;
- internal/API/async behavior, для которого не всегда есть observable artifact.

## Ожидаемый Выход Scope Analyzer

`scope-contract.md` должен содержать:

```md
## Scope Complexity Assessment
```

с оценкой факторов:

- `fields_or_blocks`;
- `conditional_dependencies`;
- `validation_domains`;
- `action_flows`;
- `integrations_api_async`;
- `status_lifecycle`;
- `expected_gaps_or_unclear`.

Решение по сложности должно быть одним из:

- `single_scope_with_internal_packages`;
- `split_into_external_scopes`.

Если выбран `single_scope_with_internal_packages`, должна быть секция:

```md
## Внутренние Рабочие Пакеты
```

Минимально ожидаемые рабочие пакеты для этого сценария:

| package_id | focus | design_method |
| --- | --- | --- |
| `WP-01` | базовые свойства полей | `field-property coverage` |
| `WP-02` | валидация ввода | `equivalence-boundary` |
| `WP-03` | условные зависимости | `dependency matrix` |
| `WP-04` | справочники и DaData UI | `field-property coverage` или `integration artifact gate` |
| `WP-05` | navigation actions | `decision table` |
| `WP-06` | интеграционные действия | `integration artifact gate` |

## Обязательные Провалы

Reviewer или eval reviewer должен считать провалом:

- scope-contract не содержит `Scope Complexity Assessment`;
- scope-contract для неоднородного раздела не содержит `Внутренние Рабочие Пакеты` и не предлагает split;
- writer создает один плоский ledger без связи `ATOM-*` с package;
- writer пишет `TC-*`, которые смешивают field properties, validation, dependencies, action flows и integration effects;
- writer помечает рабочий пакет покрытым, хотя указанный `design_method` не применен;
- интеграционный рабочий пакет закрывается `covered` без observable artifact.

## Критерии Прохождения

Eval считается пройденным, если:

- analyzer явно объяснил, почему внешний scope оставлен единым или почему предложен split;
- для единого scope есть внутренние рабочие пакеты;
- writer self-check включает package coverage и cross-package leakage;
- reviewer проверяет рабочие пакеты до sign-off;
- отсутствие рабочих пакетов для сложного scope приводит к finding.

## Регрессионный Урок

Большой scope не обязан автоматически дробиться на много внешних scopes. Но он не должен обрабатываться плоско. Если scope неоднородный, агент обязан работать внутри него по внутренним рабочим пакетам с разными методами test-design.
