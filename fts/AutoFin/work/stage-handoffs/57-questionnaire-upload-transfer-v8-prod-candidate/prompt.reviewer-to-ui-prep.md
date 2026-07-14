# Prompt: Questionnaire Upload V8 To UI Automation Prep

## Цель этапа

Подготовить отдельную automation-ready версию подписанного FT-first baseline для проверки в реальном UI, не перезаписывая canonical test cases.

## Входные артефакты

- `work/stage-handoffs/57-questionnaire-upload-transfer-v8-prod-candidate/workflow-state.yaml`;
- `test-cases/16-questionnaire-upload-transfer-v8-prod-candidate.md`;
- `work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/cycle-state.yaml`;
- `work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/outputs/final-findings.md`;
- `work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/outputs/final-traceability-matrix.md`;
- `work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/versions/signed-off/snapshot-manifest.yaml`;
- `work/stage-handoffs/57-questionnaire-upload-transfer-v8-prod-candidate/scope-coverage-gaps.md`;
- `work/stage-handoffs/57-questionnaire-upload-transfer-v8-prod-candidate/scope-clarification-requests.md`;
- `work/stage-handoffs/57-questionnaire-upload-transfer-v8-prod-candidate/promotion-receipt.v8.json`;
- `AGENT-NOTES.md`;
- `work/ui-automation-prep/UI-AGENT-NOTES.md`, если файл существует.

## Ограничения

- Не изменять FT-first baseline.
- Не закрывать `GAP-QUT-001` по наблюдению UI без source-backed уточнения byte convention.
- Не утверждать replace/reject/message для второго файла, если UI evidence не подтверждает точное поведение; различать FT/UI divergence и product defect.
- Не публиковать PII, session data или restricted evidence.

## Ожидаемый результат

Automation-ready файл и UI evidence/report либо явный `ui-prep-blocked` с blocker follow-up prompt.
