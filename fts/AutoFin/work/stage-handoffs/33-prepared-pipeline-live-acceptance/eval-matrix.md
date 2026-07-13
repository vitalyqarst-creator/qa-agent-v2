# Immutable eval matrix prepared pipeline

## Назначение

Матрица проверяет разные execution/context profiles без использования generated test cases как requirement evidence. Все package v5 загружены каноническим loader-ом с проверкой digest, artifact SHA и source registry.

| eval_id | профиль | package | obligations / gaps | package_digest | live_status |
| --- | --- | --- | ---: | --- | --- |
| `EVAL-STATIC` | `simple-field-property` | `work/review-cycles/personal-data-static-properties-hardening-validate-20260712/prepared-input/personal-data-static-properties-hardening/stage-package.json` | 15 / 0 | `4dff6cdbf3d86e5b278170dd9a56d65999dc866aa7a9ab952af0f4b2757391c7` | `validate-only-passed` |
| `EVAL-CHAR` | `character-restriction-calibration` | `work/review-cycles/personal-data-character-restrictions-shadow-v4-20260712/prepared-input/personal-data-character-restrictions-v4/stage-package.json` | 12 / 1 | `86e65b56f986973666c48eba50d2cad61aab9568dcb7dc47bc592c404048e9e9` | `accepted-not-promoted` |
| `EVAL-BOUNDARY` | `numeric-date-boundary` | `work/review-cycles/prepared-obligation-rollout-matrix-v2-20260711/prepared-input/client-addresses/stage-package.json` | 66 / 2 | `9c6e214415ac22f9bc18145c08d31adc2466fd650df19466868386fb913f52f4` | `prepared-not-run` |
| `EVAL-CONDITIONAL` | `conditional-state` | `work/review-cycles/prepared-obligation-rollout-matrix-v2-20260711/prepared-input/visual-assessment/stage-package.json` | 13 / 0 | `b37bd8602629652a6bffb9ec39ea021b6d8d8d8162ee226169c64f5c984a3d9b` | `prepared-not-run` |

## Acceptance expectations

- `EVAL-STATIC`: read-only structured writer; no gaps; no source fallback.
- `EVAL-CHAR`: 12/12 obligations, 12 unique TC, 6 UI-calibration candidates, `GAP-001`, no selected UI rejection mechanism.
- `EVAL-BOUNDARY`: preserve all numeric/input boundary points and gaps; because scope combines integration/dependency dimensions, it is a stress-eval and requires its own future immutable cycle.
- `EVAL-CONDITIONAL`: preserve every branch/state precondition; no inferred inverse branch.

## Contamination boundary

- Existing package metadata is eval input.
- Existing drafts/reviewer outputs are excluded from requirement evidence.
- Only `EVAL-CHAR` may start live in this iteration.
