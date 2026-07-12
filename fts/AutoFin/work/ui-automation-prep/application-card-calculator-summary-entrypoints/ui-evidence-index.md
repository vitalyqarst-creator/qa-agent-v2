# UI Evidence Index

## Metadata

- `ft_slug`: `AutoFin`
- `scope_slug`: `application-card-calculator-summary-entrypoints`
- `run_date`: `2026-07-12`
- `runtime`: `local-restricted-stand`
- `controlled_rerun_gate_review`: `2026-07-12`

## Evidence Policy

- `evidence_export_policy`: `local-output-index-only`
- `artifact_availability`: пути `output/` являются локальными Playwright-артефактами, не переносятся в чистый checkout и не публикуются.
- `security_classification`: `restricted-pii-and-session-risk`
- `publication_status`: `local-restricted-not-published`
- `trace_policy`: `collected-for-full-ui-run`
- `dom_seeded_policy`: `not-used`
- `normal_ui_path`: `interactive-login-and-cff-launch`
- `downstream_rule`: статусы подтверждены локальным evidence, но portable rerun заблокирован до получения безопасной fixture и sanitized evidence.
- `identity_rule`: `evidence_id` стабилен внутри этого прогона; локальный path является locator, а не переносимым идентификатором.

## Controlled Rerun Gate Audit

- `gate_status`: `blocked`
- `controlled_rerun_started`: `no`
- `new_evidence_artifacts`: `none`
- Существующие `UIE-*` относятся только к прежнему UI run и не переиспользовались для нового содержимого.
- Без нового normal UI evidence статусы `TC-ACCS-001..005` не изменялись.

## Evidence

| evidence_id | test_case_id | artifact_type | path | note | publication_status |
| --- | --- | --- | --- | --- | --- |
| `UIE-ACCS-001-SNAPSHOT-01` | `TC-ACCS-001` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-13-44-005Z.yml` | Normal UI entrypoint; содержит application data. | `local-restricted-not-published` |
| `UIE-ACCS-001-SCREENSHOT-01` | `TC-ACCS-001` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/element-2026-07-12T03-16-40-029Z.png` | Summary подтвержден, но изображение содержит персональные и документные данные. | `local-restricted-not-published` |
| `UIE-ACCS-001-SCREENSHOT-02` | `TC-ACCS-001` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-18-14-464Z.png` | Summary подтвержден, но изображение содержит персональные данные. | `local-restricted-not-published` |
| `UIE-ACCS-002-SNAPSHOT-01` | `TC-ACCS-002` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-17-54-951Z.yml` | Пять label/value пар видимы; snapshot содержит restricted application data. | `local-restricted-not-published` |
| `UIE-ACCS-002-TRACE-01` | `TC-ACCS-002` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace может содержать session state, payloads и персональные данные. | `local-restricted-not-published` |
| `UIE-ACCS-003-SCREENSHOT-01` | `TC-ACCS-003` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-18-14-464Z.png` | Карточка осталась открыта; изображение содержит персональные данные. | `local-restricted-not-published` |
| `UIE-ACCS-003-SNAPSHOT-01` | `TC-ACCS-003` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-17-54-951Z.yml` | Route не изменился; snapshot содержит restricted application data. | `local-restricted-not-published` |
| `UIE-ACCS-003-TRACE-01` | `TC-ACCS-003` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace обязательного mismatch flow; restricted. | `local-restricted-not-published` |
| `UIE-ACCS-004-SCREENSHOT-01` | `TC-ACCS-004` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-22-23-733Z.png` | Окно отсутствует; изображение списка содержит данные нескольких заявок. | `local-restricted-not-published` |
| `UIE-ACCS-004-SNAPSHOT-01` | `TC-ACCS-004` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-20-34-160Z.yml` | Выбранная local fixture и action; restricted application data. | `local-restricted-not-published` |
| `UIE-ACCS-004-TRACE-01` | `TC-ACCS-004` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace обязательного mismatch flow; restricted. | `local-restricted-not-published` |
| `UIE-ACCS-005-SCREENSHOT-01` | `TC-ACCS-005` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-22-23-733Z.png` | Prefill не наблюдаем; изображение содержит application data. | `local-restricted-not-published` |
| `UIE-ACCS-005-TRACE-01` | `TC-ACCS-005` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace blocked-observability flow; restricted. | `local-restricted-not-published` |
| `UIE-ACCS-RUN-LOG-01` | `run` | `log` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/console-2026-07-12T03-10-56-169Z.log` | Console log не используется как единственное основание статуса и не публикуется. | `local-restricted-not-published` |
| `UIE-ACCS-RUN-NETWORK-01` | `run` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.network` | Network companion может содержать headers/payloads; не публикуется. | `local-restricted-not-published` |

## Safe Evidence Required For Rerun

- screenshots только с синтетическими данными или с проверенной маскировкой PII;
- trace/network capture без authorization headers, cookies, session storage и чувствительных payloads;
- переносимая synthetic fixture с безопасным идентификатором и documented setup/reset path.
