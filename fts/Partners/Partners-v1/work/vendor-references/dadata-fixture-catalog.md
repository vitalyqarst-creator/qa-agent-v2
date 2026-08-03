# Partners-v1 DaData fixture catalog

## Scope

Verified DaData fixtures for `fts/Partners/Partners-v1`.

These fixtures are token-free evidence. API keys/secrets are not stored.

## Party fixtures

| Fixture ID | Endpoint | Query | Expected suggestion | ИНН | КПП | ОГРН | Юридический адрес | Response SHA-256 | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FX-DADATA-PARTY-ROMASHKA-A-001` | `suggest/party` | `4909128502` | `ООО "РОМАШКА"` | `4909128502` | `490901001` | `1184910001462` | `г Магадан, ул Речная, д 3, помещ 9/5` | `ce4178f2fe2d1369a04de230e986fdc906ccf1a42698a59bf4ed5f28431f75dc` | `work/vendor-references/dadata-fixtures/FX-DADATA-PARTY-ROMASHKA-A-001/FX-DADATA-PARTY-ROMASHKA-A-001.verification.json` |
| `FX-DADATA-PARTY-ROMASHKA-B-001` | `suggest/party` | `2622004340` | `ООО "РОМАШКА"` | `2622004340` | `262201001` | `1032601491658` | `Ставропольский край, село Летняя Ставка, ул Чехова, д 23А, офис А` | `adf097b52fa108550e1c42bdaa7223c482b69dc8052636912441e593ecaa793f` | `work/vendor-references/dadata-fixtures/FX-DADATA-PARTY-ROMASHKA-B-001/FX-DADATA-PARTY-ROMASHKA-B-001.verification.json` |

## Usage notes

- `FX-DADATA-PARTY-ROMASHKA-A-001` and `FX-DADATA-PARTY-ROMASHKA-B-001` intentionally have the same expected suggestion and different `ИНН`; this is useful for duplicate-key boundary checks where `Наименование + ИНН` is the uniqueness key.
- Test cases must not ask the tester to call DaData during execution. Use the fixture query and expected suggestion/components from this catalog.
- If the UI does not allow preserving the same `ИНН` while changing the partner name manually, tests for "same ИНН, different name" require either backend-seeded data or UI calibration.
