# Prepared Compiler Matrix After Obligation Remediation

## Результат

Все девять исходных AutoFin compiler inputs собраны без semantic degradation. Единственный fast-eligible пакет исходной матрицы — ранее доказанный widget-selection; остальные восемь корректно остаются `standard-required`.

| scope | obligations | gaps | dictionaries | execution_profile | unsupported_dimensions |
| --- | ---: | ---: | ---: | --- | --- |
| `widget-selection` | 6 | 2 | 0 | `simple-field-property` | `none` |
| `calculator-summary` | 4 | 1 | 0 | `standard-required` | `state-transition-or-navigation` |
| `common-actions` | 1 | 0 | 0 | `standard-required` | `state-transition-or-navigation` |
| `search-clear` | 4 | 0 | 0 | `standard-required` | `limited-default-oracle`; `state-transition-or-navigation` |
| `visual-assessment` | 13 | 0 | 9 | `standard-required` | `dependency-state` |
| `print-form` | 21 | 6 | 5 | `standard-required` | `dependency-state`; `generated-document`; `repeatable-lifecycle` |
| `client-addresses` | 66 | 2 | 0 | `standard-required` | `dependency-state`; `evidence-qualified-evidence`; `expected-result`; `input-boundaries`; `integration-persistence`; `numeric-boundaries` |
| `document-files` | 50 | 5 | 1 | `standard-required` | `dependency-state`; `evidence-qualified-evidence`; `file-upload`; `integration-persistence`; `numeric-boundaries`; `repeatable-lifecycle`; `state-transition-or-navigation` |
| `document-recognition` | 9 | 1 | 1 | `standard-required` | `dependency-state`; `evidence-qualified-fixture`; `evidence-qualified-fixture-evidence`; `file-upload`; `integration-persistence`; `state-transition-or-navigation` |

## Второй fast canary

Ни один из восьми альтернативных полных scope не подходит для fast path. Для независимой live-проверки подготовлена eval-only проекция `14-prepared-canary-client-address-static-properties` из подтверждённого scope client-addresses.

| candidate | obligations | gaps | profile | boundary |
| --- | ---: | ---: | --- | --- |
| `client-address-static-properties` | 6 | 0 | `simple-field-property` | unconditional visibility and initial values only |

Проекция исключает conditional, numeric, integration, persistence, navigation и inverse-branch behavior. Она не заменяет полный signed-off client-addresses baseline и не может быть promoted поверх него.

## Evidence

- Matrix packages: `fts/AutoFin/work/review-cycles/prepared-obligation-rollout-matrix-v2-20260711/prepared-input/`.
- Canary compiler input: `fts/AutoFin/work/stage-handoffs/25-prepared-obligation-rollout/compiler-inputs/client-address-static-properties/compiler-input.yaml`.
- Canary package v1: `fts/AutoFin/work/review-cycles/codex-exec-prepared-client-address-static-live-v1-20260711/prepared-input/client-address-static-v1/stage-package.json`.
- Production canary target was absent after compilation.
