# Atomic Requirements Ledger

Eval-only projection of source-backed static properties from the confirmed external scope `application-card-client-addresses`. Conditional, numeric, integration, persistence and address-composition atoms are explicitly excluded from this canary projection and remain in the full scope package.

| atom_id | package_id | source_refs | req_id | atomic_statement | coverage_status | covered_by_tc | priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `WP-01` | `SRC-001` | `no_requirement_code:SRC-001` | Блок `Адреса клиента` отображается в заявке. | `covered` | `TC-CASP-001` | `High` |
| `ATOM-002` | `WP-01` | `SRC-002` | `BSR 107` | `Адрес регистрации` видим всегда. | `covered` | `TC-CASP-002` | `High` |
| `ATOM-003` | `WP-01` | `SRC-003` | `BSR 113` | Переключатель `Адрес регистрации / Ввести вручную` видим всегда. | `covered` | `TC-CASP-003` | `Medium` |
| `ATOM-004` | `WP-01` | `SRC-003` | `BSR 114` | Значение по умолчанию для `Адрес регистрации / Ввести вручную` равно `Нет`. | `covered` | `TC-CASP-004` | `Medium` |
| `ATOM-005` | `WP-01` | `SRC-014` | `BSR 130` | `Адрес фактического места жительства совпадает с адресом регистрации` видим всегда. | `covered` | `TC-CASP-005` | `Medium` |
| `ATOM-006` | `WP-01` | `SRC-014` | `BSR 131` | Значение по умолчанию для совпадения фактического адреса с адресом регистрации равно `Да`. | `covered` | `TC-CASP-006` | `High` |
