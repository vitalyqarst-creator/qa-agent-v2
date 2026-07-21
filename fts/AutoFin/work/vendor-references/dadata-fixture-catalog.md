# DaData Fixture Catalog

## Политика

- Каталог подготавливается до writer; runtime TC не запрашивает новый fixture.
- Positive и negative fixtures допускаются в production-ready TC только после
  live-проверки и сохранения полного response snapshot без секретов.
- Перед release выполняется recheck. DaData сообщает, что адресный справочник
  обновляется еженедельно, поэтому срок свежести — 7 дней.
- Negative fixture без сохранённого `suggestions=[]` имеет статус
  `blocked-verification` и не допускается в production-ready TC.

## Fixtures

| fixture_id | outcome | exact query | exact suggestion | source/snapshot | checked_at | response_sha256 | freshness | status | linked_tcs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FX-DADATA-ADDR-POS-001` | `suggestions-found` | `самара авроры 7 12` | `г Самара, ул Авроры, д 7, кв 12` | `dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json`; `dadata-fixtures/FX-DADATA-ADDR-POS-001.verification.json` | `2026-07-21T07:36:53.323305Z` | `1e889abe30cd94b7f83fd847167e9848472a4837bf2a88978c56f53e45b7058a` | recheck before release; stale after 7 days | `verified-live-response` | `TC-003`; `TC-010`; `TC-061`; `TC-066`; `TC-111` |
| `FX-DADATA-REGION-POS-001` | `suggestions-found` | `Саратов`; `from_bound=region`; `to_bound=region` | `Саратовская обл` | `dadata-fixtures/FX-DADATA-REGION-POS-001.response.json`; `dadata-fixtures/FX-DADATA-REGION-POS-001.verification.json` | `2026-07-21T07:37:03.725180Z` | `1a6cffc2b87187995bd90db4e4acbae13dbadc9812cf56a5aa2d0906d7d120d3` | recheck before release; stale after 7 days | `verified-live-response` | `TC-024`; `TC-080` |
| `FX-DADATA-ADDR-NEG-001` | `suggestions-empty` | `ZZZNOADDRESS7F3A9C2E20260721` | `not_applicable` | `dadata-fixtures/FX-DADATA-ADDR-NEG-001.response.json`; `dadata-fixtures/FX-DADATA-ADDR-NEG-001.verification.json` | `2026-07-21T05:37:39.108400Z` | `8e5e36d9bf781113e259d054939c9dfefe858cc0240844aa224405d7a69f482e` | recheck before release; stale after 7 days | `verified-live-response` | `TC-009`; `TC-065` |

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
