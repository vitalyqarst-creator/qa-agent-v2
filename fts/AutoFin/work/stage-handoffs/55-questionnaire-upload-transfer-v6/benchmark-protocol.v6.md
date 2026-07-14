# V6 Transfer Canary Protocol

## Цель

Проверить переносимость prepared package v8 и context projection на новом current-source file-upload scope, не использовавшемся для настройки V3-V5.

## Один запуск

- fresh cycle `questionnaire-upload-transfer-v6-20260714`;
- backend `exec`; 11 obligations; 10 planned TC;
- один writer и один independent reviewer в разных sessions;
- один dispatcher invocation; retry/resume/repair/rebind/sharding/SDK fallback запрещены.

## Quality Gates

- package compiled from current `FT4AutoFinFinal.*`, BSR 206-211;
- reviewer: 11/11 covered, incorrect=0, error findings=0;
- unique IDs/titles; exact negative message retained;
- package context projection removes DaData only as not applicable;
- no production mutation; `fts/AutoFin/test-cases/16-questionnaire-upload-transfer-v6.md` remains absent.

## Performance

- publish duration, uncached tokens/OBL and exact context projection bytes;
- quality dominates speed; no retry may be selected by performance;
- one canary proves transfer behavior, not a stable median.
