# Выбор второго prepared canary

## Контекст

- Родительский подтверждённый scope: `application-card-client-addresses`.
- Основные источники и parity: handoff `09-application-card-client-addresses`.
- Актуальная source selection: handoff `20-prepared-autofin-cross-scope/source-selection.md` с обязательными DOCX и XHTML.
- Режим: eval-only проекция одного внутреннего пакета, не новый production baseline.

## Граница canary

Включены только шесть независимо наблюдаемых статических обязанностей:

- отображение блока адресов;
- видимость адреса регистрации;
- видимость и default переключателя ручного ввода адреса регистрации;
- видимость и default признака совпадения фактического адреса с адресом регистрации.

Исключены conditional visibility, requiredness, numeric/length, DaData, composition, persistence, navigation и любые inverse branches. Они остаются в полном `application-card-client-addresses` пакете с route `standard-required`.

## Решение

- Canary не имеет открытых coverage gaps внутри выбранной статической проекции.
- Canary не может быть promoted поверх `test-cases/14-application-card-client-addresses.md`.
- Целевой путь `test-cases/14-prepared-canary-client-address-static-properties.md` используется только для проверки promotion contract и должен оставаться отсутствующим во время live-canary.
- Fast eligibility определяется компилятором; ручное override запрещено.
