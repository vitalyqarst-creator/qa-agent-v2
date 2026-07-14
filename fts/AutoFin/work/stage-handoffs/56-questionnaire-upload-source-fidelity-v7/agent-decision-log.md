# Agent Decision Log — Questionnaire Upload Source Fidelity V7

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v7` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/55-questionnaire-upload-transfer-v6/prompt.v6-to-next.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `post-canary-source-package-audit.v6.md` | Ограничить V7 двумя доказанными классами искажения: literal и unit conversion. | V6 дал два воспроизводимых source-to-package дефекта; general semantic equivalence checker был бы недоказуемым и хрупким. | `references/agent/source-to-package-fidelity-format.md`; compiler gate | `high` | `applied` |
| `DEC-002` | 2 | `gap` | `BSR 210`: `размер файла не более 40 МБ` | Не выводить decimal/binary byte convention; создать `GAP-QUT-001`. | Final FT не содержит policy, позволяющей выбрать точное число байт. | `scope-coverage-gaps.md`; `ATOM-008`; `OBL-QUT-008`; `FID-QUT-002` | `high` | `applied` |
| `DEC-003` | 3 | `coverage` | V6 ledger: 11 source obligations | Сохранить 11 obligations; boundary obligation остается gap, а не удаляется. | Уменьшение числа obligations скрыло бы потерю самостоятельной обязанности ФТ. | V7 ledger и prepared `atomic-obligations.json` | `high` | `applied` |
| `DEC-004` | 4 | `test-design` | Oversize negative source rule | Использовать portable fixture `50 МБ` без точного byte value. | Такой fixture больше 40 МБ при обеих распространенных conventions и не выдается за boundary продукта. | `negative-oracle-inventory.md`; `PLAN-QUT-008`; `FID-QUT-003` | `medium: fixture generator must preserve a size above both thresholds` | `applied` |
| `DEC-005` | 5 | `artifact-write` | H56 создает table-heavy scope/compiler artifacts | Генерировать Markdown через committed builder и `scripts/write_artifact_sections.py --manifest`. | Это соответствует объявленной Artifact Write Strategy и дает воспроизводимые manifests. | `scripts/build_autofin_questionnaire_upload_source_fidelity_v7.py`; H56 `_artifact_write/**` | `high` | `applied` |
| `DEC-006` | 6 | `validation` | Initial scoped validator: 4 errors | Исправить canonical prompt headings/links и negative-oracle schema; переписать audit logs по canonical format. | Ошибки были в handoff schema, не в source obligations; routing до исправления недопустим. | `prompt.scope-gaps-to-reviewer.md`; `negative-oracle-inventory.md`; logs | `high` | `applied` |
| `DEC-007` | 7 | `routing` | Один non-blocking gap остается open | Завершить H56 как `ready-for-gap-review`, `next_skill = ft-test-case-reviewer`; live не разрешать. | Scope contract требует reviewer gap check до writer; V7 не является live authorization. | `workflow-state.yaml`; `prompt.scope-gaps-to-reviewer.md` | `high` | `applied` |
| `DEC-008` | 8 | `validation` | Self-review byte-policy branch | Требовать integer `byte_offset` и проверять exact bytes как `unit_value * base + offset`. | Непустой policy locator без arithmetic check мог формально пропустить неверную decimal/binary проекцию. | compiler diagnostic `source-fidelity-byte-conversion-mismatch`; regression test | `high` | `applied` |
