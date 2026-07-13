# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/43-personal-data-v6-output-capacity/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V6 terminal `blocked-quality-gate`; 43 TC не имеют deterministic findings | Создать новый immutable H44/V7, не retry/resume V6 | Stop gate запрещает replay; новый cycle сохраняет проверяемую lineage | H44; будущий V7 cycle | high | applied |
| `DEC-002` | 2 | `source-boundary` | V6 merged draft — generated unsigned output; V7 package остаётся source-backed | Использовать V6 draft только как hash-bound repair input, не как requirement evidence | Это позволяет сохранить корректные секции без подмены DOCX/XHTML и prepared evidence | repair plan | high | applied |
| `DEC-003` | 3 | `validation` | V6 package содержал заранее распознаваемые non-observable oracle | Добавить prepared oracle-quality preflight до любой writer session | Late gate израсходовал 4 sessions на дефект, который детерминированно виден до live | runner preflight; evals | high | applied |
| `DEC-004` | 4 | `artifact-write` | Quality findings содержат точные TC IDs | Разрешить одну fresh targeted repair session и runner-owned splice с byte-preservation proof | Повторная генерация 47 TC не оправданна | repair plan/validator/splice | high | applied |
| `DEC-005` | 5 | `live-gate` | Oracle/repair evals, V7 validate-only и exec dry-run прошли | После checkpoint/push разрешить ровно один V7 dispatcher | Одноразовый live проверяет реальный transport, но не расширяет recovery authority | pre-live stop gate; authorization | high | applied |
| `DEC-006` | 6 | `artifact-write` | Targeted writer вернул exact 4 TC; splice/gates прошли | Принять runner-owned merged draft только как unsigned reviewer input | `43` non-target секции byte-preserved; `65/65` obligations прошли deterministic gates | V7 repair validator/splice | high | applied |
| `DEC-007` | 7 | `validation` | Reviewer применил `invented-coverage` к testable `OBL-025` | Завершить V7 как `blocked-invalid-output`; не retry/resume | Status-specific contract нарушен, sign-off отсутствует | V7 cycle state; live result | high | applied |
| `DEC-008` | 8 | `source-boundary` | Отклонённый reviewer ответ содержит `F-001..F-005`; `F-002` противоречит `DICT-001` evidence | Считать findings диагностикой, а не authoritative review; повторно проверять их по source evidence | Invalid output нельзя повышать до sign-off; ложный `F-002` доказывает необходимость evidence guard | live blocker analysis | high | applied |
| `DEC-009` | 9 | `routing` | Writer route прошёл, но generic reviewer schema и metadata gate недостаточны | Следующий successor — новый V8 с schema/evidence/metadata remediation до любого live | Повтор V7 воспроизведёт те же риски и нарушит stop gate | successor prompt | high | proposed |
