# Manual UI Confirmation Evidence

Date: 2026-07-30

Source: user manual UI check on the same test stand.

Confirmed manually:

- TC-DOC-019: drag-and-drop upload for `Анкета клиента` works as expected.
- TC-DOC-025: drag-and-drop upload for `Паспорт клиента` works as expected.
- TC-DOC-031: drag-and-drop upload for `Второй документ` works as expected.
- TC-DOC-022 / TC-DOC-028 / TC-DOC-033: upload of a document larger than 40 MB by button and by drag-and-drop shows expected validation behavior.

Exact observed message for >40 MB / invalid requirements:

```text
Документы не загружены. Проверьте соответствуют ли документы требованиям: формат pdf, размер не более 40 МБ
```

QR upload status:

- TC-DOC-020 and TC-DOC-026 remain blocked because QR upload functionality is not implemented end-to-end yet.

Screenshot evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/docs-30-manual-over40-dnd-expected-message.png`
