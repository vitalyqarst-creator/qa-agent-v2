# Pre-Live Test Report V6

## Итог

`pass-checkpoint-pending`: semantic, package, artifact и architecture offline gates прошли. Live остаётся запрещён до pushed checkpoint и отдельного hash-bound authorization.

## Проверки

| check | result | evidence |
| --- | --- | --- |
| Focused compiler/runner suites | `178 passed` | `tests.test_prepared_workflow_compiler`; `tests.test_codex_exec_review_cycle_runner` |
| Full discovery suite | `1016 passed; 1 skipped` | final-code rerun: `python -m unittest discover -s tests -p 'test_*.py'` |
| Scoped artifact audit | `0 errors; 0 warnings; 3 expected source-quality info` | H55, audit session-log and strict decision-log policies |
| Architecture audit | `61 checks; 0 findings` | canonical auditor helper |
| Prepared compile | `11 obligations; 0 gaps; 10 planned TC` | package `questionnaire-upload-transfer-v6-r1` |
| Exec capability dry-run | `selected=exec; verified=true; fallback=false` | `backend-selection.v6-r1.dry-run.json` |
| Runner validate-only | `validated` | package v8; structured writer; compact reviewer; target absent |
| Context projection | `pass` | writer removed 5 265 irrelevant bytes; reviewer relevance is evaluated before truncation; no obligation/oracle/fixture reduction |
| Generic reference-only regression | `pass` | `fixture_values=()` when plan names no exact value |

## Immutable Candidate Identities

| artifact | identity |
| --- | --- |
| stage package SHA-256 | `8d30cc27da9a16d3c162c76d847b4e4c582d54720273bdcdc502f0f3458ff106` |
| package digest | `c0a6cb07676ca3d7ae3617289dcf4712f100c3ca510a0b4732e58a9b961cb32d` |
| input fingerprint | `f60a5bdf97689cfdcd87860c0c7b55f9199663886cf83ee201c5f3f6b2a13b2c` |
| atomic obligations SHA-256 | `b2e92672e1a528e2bb7597375390dbdf228746540af6dde48b219afd35d4639d` |
| dispatcher config SHA-256 | `14522560aeead43741aae243870bfbe719c5731903ca7d295e5cf5c8430f09a5` |

## Production Boundary

| path | expected |
| --- | --- |
| `test-cases/14-application-card-documents-and-questionnaire-files.md` | SHA-256 `2a82f3bab1949ff6c07bc0fd1e46d5311edcf842d8d93247e6f5950a66b9df49` |
| `test-cases/section-18-visual-assessment-criteria.md` | SHA-256 `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc` |
| `test-cases/14-application-card-client-personal-data.md` | SHA-256 `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc` |
| `test-cases/section-4.2-applications-menu-search.md` | SHA-256 `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3` |
| `test-cases/16-questionnaire-upload-transfer-v6.md` | absent |

## Stop Decision

Offline blocker отсутствует. Следующий допустимый шаг: commit/push именно этого offline состояния, проверка local/origin equality, затем отдельный authorization artifact на один invocation.
