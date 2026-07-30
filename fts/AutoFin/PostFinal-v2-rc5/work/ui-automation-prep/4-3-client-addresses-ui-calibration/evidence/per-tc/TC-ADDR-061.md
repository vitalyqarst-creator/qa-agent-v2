# TC-ADDR-061

Status: mismatch-ft-ui

Checked: actual `Улица` requiredness.

UI actions: enabled actual address manual mode, left `Улица` empty, clicked `ДАЛЕЕ`.

Trigger: `ДАЛЕЕ`.

Observed UI reaction:

- `Улица` has no required marker.
- Empty `Улица` remains valid.
- No inline message is shown.
- Other required fields block transition, but `Улица` itself is not a validation blocker.

Mismatch: baseline expectation that actual `Улица` is required does not match UI behavior.

Required correction: mark actual `Улица` optional in expected result/preconditions.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-required-empty-after-next.png`
