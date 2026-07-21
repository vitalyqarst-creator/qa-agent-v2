# DaData Fixture Catalog

## Политика

- Каталог подготавливается до writer; runtime TC не запрашивает новый fixture.
- Документационные positive fixtures — representative values, не полный справочник.
- Перед release выполняется recheck. DaData сообщает, что адресный справочник
  обновляется еженедельно, поэтому срок свежести — 7 дней.
- Negative fixture без сохранённого `suggestions=[]` имеет статус
  `blocked-verification` и не допускается в production-ready TC.

## Fixtures

| fixture_id | outcome | exact query | exact suggestion | source/snapshot | checked_at | response_sha256 | freshness | status | linked_tcs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FX-DADATA-ADDR-POS-001` | `suggestions-found` | `самара авроры 7 12` | `443017, Самарская обл, г Самара, ул Авроры, д 7, кв 12` | `dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json` | `2026-07-21` | `fb3ec0888ae6f47b21659c5654634b529302342112b0b3c5ba5fdb102c74abe2` | recheck before release; stale after 7 days | `verified-documentation-example` | `TC-003`; `TC-010`; `TC-061`; `TC-066`; `TC-111` |
| `FX-DADATA-REGION-POS-001` | `suggestions-found` | `Саратов`; `from_bound=region`; `to_bound=region` | `Саратовская обл` | `dadata-fixtures/FX-DADATA-REGION-POS-001.response.json` | `2026-07-21` | `f7256c3082eaf5374112890bd9c43a27694a3e75b3f9a471983ecef47ea62e34` | recheck before release; stale after 7 days | `verified-vendor-support-example` | `TC-024`; `TC-080` |
| `FX-DADATA-ADDR-NEG-001` | `suggestions-empty` | `not_verified` | `not_applicable` | `dadata-fixtures/negative-fixture-verification-request.md` | `not_verified` | `not_verified` | verify immediately before writer and release | `blocked-verification` | `TC-009`; `TC-065` |

## Exact Components: FX-DADATA-ADDR-POS-001

- Индекс: `443017`.
- Регион: `Самарская обл`.
- Город: `г Самара`.
- Улица: `ул Авроры`.
- Дом: `7`.
- Квартира: `12`.

## Release Reconciliation

Если recheck возвращает другое предложение или компоненты, не регистрировать
дефект AutoFin автоматически. Сначала сохранить новый response snapshot, обновить
SHA-256 и точные literals fixture/TC, затем повторить продуктовую проверку.
