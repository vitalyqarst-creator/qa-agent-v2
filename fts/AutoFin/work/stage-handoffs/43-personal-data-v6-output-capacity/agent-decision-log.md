# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/42-personal-data-v5-source-first-recovery/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V5 `blocked-input`; draft отсутствует; 47 TC требовались в одном schema-constrained ответе | Не повторять и не возобновлять V5; создать новый immutable V6 cycle | Повтор one-shot transport не устраняет output-capacity blocker и нарушает stop gate | H43; будущий V6 cycle | high | applied |
| `DEC-002` | 2 | `validation` | В V5 проверялся размер входного контекста, но не размер требуемого ответа | Добавить отдельный output-capacity preflight до любой live-сессии | Input budget не доказывает, что один ответ вместит полный draft | runner capacity report; regression evals | high | applied |
| `DEC-003` | 3 | `artifact-write` | 65 testable obligations образуют 47 групп TC | Разбивать только по целым `planned_test_case_id`, запускать каждый shard в новой сессии и объединять runner-ом | Ни один TC и ни одно obligation не должны делиться между writer-сессиями; merge не требует доменного решения | shard plan; shard attempts; merge manifest | high | applied |
| `DEC-004` | 4 | `source-boundary` | H42 source-first boundary; GAP-001..003 не блокируют FT-first writing | Не обращаться к стенду и не использовать V1-V5 drafts как requirement evidence | Все writer semantics уже находятся в immutable prepared package; стенд относится к UI-prep | V6 prepared package and shard projections | high | applied |
| `DEC-005` | 5 | `routing` | Требование независимого semantic review | Запускать reviewer только после полного merge и всех детерминированных full-set gates | Review отдельных shards не заменяет проверку согласованности полного набора | V6 reviewer attempt | high | applied |
| `DEC-006` | 6 | `validation` | Corrected V6 preflight: 4 shards, `47 TC / 65 OBL`, writer prompts 48–57 KiB | Разрешить переход к checkpoint; сохранить отдельные reviewer context/output capacity gates | One-shot blocker устранён до live, а reviewer не должен стать следующим поздним capacity blocker | `output-capacity-preflight.v6.json`; `pre-live-test-report.md` | high | applied |
| `DEC-007` | 7 | `routing` | 132 целевых tests pass; полный suite содержит только два оставшихся fixture-dependent infra failures | Не считать отсутствие unrelated test fixture blocker-ом V6, но явно сохранить как инфраструктурный долг | Оба failure не затрагивают runner/compiler/V6 и были известны до итерации; скрывать их нельзя | `pre-live-test-report.md` | risk:unrelated-full-suite-not-green | applied |
