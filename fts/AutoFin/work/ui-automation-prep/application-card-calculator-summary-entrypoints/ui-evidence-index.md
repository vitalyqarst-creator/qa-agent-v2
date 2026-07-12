# UI Evidence Index

## Metadata

- `ft_slug`: `AutoFin`
- `scope_slug`: `application-card-calculator-summary-entrypoints`
- `run_date`: `2026-07-12`
- `runtime`: `local-restricted-stand`

## Evidence Policy

- `evidence_export_policy`: `local-output-index-only`
- `artifact_availability`: пути `output/` являются локальными Playwright-артефактами, не переносятся в чистый checkout и не публикуются.
- `security_classification`: `restricted-pii-and-session-risk`
- `publication_status`: `local-restricted-not-published`
- `trace_policy`: `collected-for-full-ui-run`
- `dom_seeded_policy`: `not-used`
- `normal_ui_path`: `interactive-login-and-cff-launch`
- `downstream_rule`: статусы подтверждены локальным evidence, но portable rerun заблокирован до получения безопасной fixture и sanitized evidence.

## Evidence

| test_case_id | artifact_type | path | note | publication_status |
| --- | --- | --- | --- | --- |
| `TC-ACCS-001` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-13-44-005Z.yml` | Normal UI entrypoint; содержит application data. | `local-restricted-not-published` |
| `TC-ACCS-001` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/element-2026-07-12T03-16-40-029Z.png` | Summary подтвержден, но изображение содержит персональные и документные данные. | `local-restricted-not-published` |
| `TC-ACCS-001` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-18-14-464Z.png` | Summary подтвержден, но изображение содержит персональные данные. | `local-restricted-not-published` |
| `TC-ACCS-002` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-17-54-951Z.yml` | Пять label/value пар видимы; snapshot содержит restricted application data. | `local-restricted-not-published` |
| `TC-ACCS-002` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace может содержать session state, payloads и персональные данные. | `local-restricted-not-published` |
| `TC-ACCS-003` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-18-14-464Z.png` | Карточка осталась открыта; изображение содержит персональные данные. | `local-restricted-not-published` |
| `TC-ACCS-003` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-17-54-951Z.yml` | Route не изменился; snapshot содержит restricted application data. | `local-restricted-not-published` |
| `TC-ACCS-003` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace обязательного mismatch flow; restricted. | `local-restricted-not-published` |
| `TC-ACCS-004` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-22-23-733Z.png` | Окно отсутствует; изображение списка содержит данные нескольких заявок. | `local-restricted-not-published` |
| `TC-ACCS-004` | `snapshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-20-34-160Z.yml` | Выбранная local fixture и action; restricted application data. | `local-restricted-not-published` |
| `TC-ACCS-004` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace обязательного mismatch flow; restricted. | `local-restricted-not-published` |
| `TC-ACCS-005` | `screenshot` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/page-2026-07-12T03-22-23-733Z.png` | Prefill не наблюдаем; изображение содержит application data. | `local-restricted-not-published` |
| `TC-ACCS-005` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.trace` | Trace blocked-observability flow; restricted. | `local-restricted-not-published` |
| `run` | `log` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/console-2026-07-12T03-10-56-169Z.log` | Console log не используется как единственное основание статуса и не публикуется. | `local-restricted-not-published` |
| `run` | `trace` | `output/playwright/application-card-calculator-summary-entrypoints/.playwright-cli/traces/trace-1783825972365.network` | Network companion может содержать headers/payloads; не публикуется. | `local-restricted-not-published` |

## Safe Evidence Required For Rerun

- screenshots только с синтетическими данными или с проверенной маскировкой PII;
- trace/network capture без authorization headers, cookies, session storage и чувствительных payloads;
- переносимая synthetic fixture с безопасным идентификатором и documented setup/reset path.
