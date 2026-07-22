# DaData Fixture Catalog

## Политика

- Каталог подготавливается до writer; runtime TC не запрашивает новый fixture.
- Positive и negative fixtures допускаются в production-ready TC только после
  live-проверки и сохранения полного response snapshot без секретов.
- После успешной live-проверки fixture получает lifecycle
  `verified-once / revalidate-on-failure`: `checked_at` и SHA-256 фиксируют
  первоначальное evidence, но не образуют срок годности.
- Release-preflight, writer и reviewer используют сохранённые snapshot/literals и
  не выполняют автоматические live-вызовы DaData.
- Повторная live-проверка допускается только после фактического падения связанного
  теста, подтверждённого изменения API/контракта DaData или явного запроса
  пользователя.
- Negative fixture без сохранённого `suggestions=[]` имеет статус
  `blocked-verification` и не допускается в production-ready TC.

## Fixtures

| fixture_id | outcome | exact query | exact suggestion | source/snapshot | checked_at | response_sha256 | lifecycle | status | linked_tcs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FX-DADATA-ADDR-POS-001` | `suggestions-found` | `самара авроры 7 12` | `г Самара, ул Авроры, д 7, кв 12` | `dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json`; `dadata-fixtures/FX-DADATA-ADDR-POS-001.verification.json` | `2026-07-21T07:36:53.323305Z` | `1e889abe30cd94b7f83fd847167e9848472a4837bf2a88978c56f53e45b7058a` | `verified-once / revalidate-on-failure` | `verified-live-response` | `TC-003`; `TC-010`; `TC-061`; `TC-066`; `TC-111` |
| `FX-DADATA-REGION-POS-001` | `suggestions-found` | `Саратов`; `from_bound=region`; `to_bound=region` | `Саратовская обл` | `dadata-fixtures/FX-DADATA-REGION-POS-001.response.json`; `dadata-fixtures/FX-DADATA-REGION-POS-001.verification.json` | `2026-07-21T07:37:03.725180Z` | `1a6cffc2b87187995bd90db4e4acbae13dbadc9812cf56a5aa2d0906d7d120d3` | `verified-once / revalidate-on-failure` | `verified-live-response` | `TC-024`; `TC-080` |
| `FX-DADATA-ADDR-NEG-001` | `suggestions-empty` | `ZZZNOADDRESS7F3A9C2E20260721` | `not_applicable` | `dadata-fixtures/FX-DADATA-ADDR-NEG-001.response.json`; `dadata-fixtures/FX-DADATA-ADDR-NEG-001.verification.json` | `2026-07-21T05:37:39.108400Z` | `8e5e36d9bf781113e259d054939c9dfefe858cc0240844aa224405d7a69f482e` | `verified-once / revalidate-on-failure` | `verified-live-response` | `TC-009`; `TC-065` |
| `FX-DADATA-FMS-POS-001` | `suggestions-found` | `772-053` | `ОВД ЗЮЗИНО Г. МОСКВЫ`; code=`772-053`; region_code=`77`; type=`2` | `dadata-fixtures/FX-DADATA-FMS-POS-001/FX-DADATA-FMS-POS-001.response.json`; `dadata-fixtures/FX-DADATA-FMS-POS-001/FX-DADATA-FMS-POS-001.verification.json` | `2026-07-21T14:06:27.177461Z` | `5575e4fbb9e28df33d8826a00580594eccde839bb6d625bfa84a6bf53d2bf90e` | `verified-once / revalidate-on-failure` | `verified-live-response` | `pending-passport-writer` |
| `FX-DADATA-PARTY-ACTIVE-001` | `suggestions-found` | `7707083893` | `ПАО СБЕРБАНК`; status=`ACTIVE`; ОПФ=`ПАО` | `dadata-fixtures/FX-DADATA-PARTY-ACTIVE-001/FX-DADATA-PARTY-ACTIVE-001.response.json`; `dadata-fixtures/FX-DADATA-PARTY-ACTIVE-001/FX-DADATA-PARTY-ACTIVE-001.verification.json` | `2026-07-21T19:55:46.360582Z` | `ea5fe50291bb48b1114c6560ac6ec4196c5f79f99e9f609da594b4847dd0d9b0` | `verified-once / revalidate-on-failure` | `verified-live-response` | `pending-employment-writer` |
| `FX-DADATA-PARTY-LIQUIDATED-001` | `suggestions-found` | `7733073764` | `ФОРМАД-ПЛАСТ ООО 7701`; status=`LIQUIDATED`; ОПФ=`ООО` | `dadata-fixtures/FX-DADATA-PARTY-LIQUIDATED-001/FX-DADATA-PARTY-LIQUIDATED-001.response.json`; `dadata-fixtures/FX-DADATA-PARTY-LIQUIDATED-001/FX-DADATA-PARTY-LIQUIDATED-001.verification.json` | `2026-07-21T19:56:15.453318Z` | `24f9823c19ddefcdd76b132cda96a4543212d5427fccebc42507d35122d3b3e4` | `verified-once / revalidate-on-failure` | `verified-live-response` | `pending-employment-writer` |

## Exact Components: FX-DADATA-ADDR-POS-001

- Индекс: `443017`.
- Регион: `Самарская обл`.
- Город: `г Самара`.
- Улица: `ул Авроры`.
- Дом: `7`.
- Квартира: `12`.

## Exact Components: FX-DADATA-FMS-POS-001

- Код подразделения: `772-053`.
- Наименование подразделения: `ОВД ЗЮЗИНО Г. МОСКВЫ`.
- Код региона: `77`.
- Тип подразделения: `2`.
- В сохранённом ответе присутствуют как минимум два предложения; fixture пригоден
  для проверки BSR 95 без runtime-вызова DaData из тест-кейса.

## Exact Components: FX-DADATA-PARTY-ACTIVE-001

- ИНН: `7707083893`.
- КПП: `773601001`.
- Наименование: `ПАО СБЕРБАНК`.
- Статус: `ACTIVE`.
- ОПФ: `ПАО`.

## Exact Components: FX-DADATA-PARTY-LIQUIDATED-001

- ИНН: `7733073764`.
- КПП: `773301001`.
- Наименование: `ФОРМАД-ПЛАСТ ООО 7701`.
- Статус: `LIQUIDATED`.
- ОПФ: `ООО`.

## Revalidation On Failure

Повторная live-проверка не является release-preflight gate. Verification scripts
остаются ручными диагностическими инструментами и не вызываются автоматически.

Если после падения связанного теста повторная проверка возвращает другое
предложение или компоненты, не регистрировать дефект AutoFin автоматически.
Сначала сохранить новое immutable evidence, обновить активную привязку SHA-256 и
точные literals fixture/TC, затем повторить продуктовую проверку.
