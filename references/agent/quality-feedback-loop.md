# Quality Feedback Loop

## Назначение

Этот reference описывает, как превращать повторяющиеся провалы качества тест-кейсов в проверяемые eval targets и bounded задачи на улучшение agent-layer.

Цель не в том, чтобы после каждого замечания дописывать новые общие инструкции. Цель - собрать evidence, выделить повторяемый failure pattern, проверить его через eval и только потом менять `skills/`, `references/`, `scripts/` или `tests/`.

## Базовый принцип

Улучшение начинается с reviewed correction, а не с общего недовольства качеством.

Сырой сигнал вроде "кейсы плохие" недостаточен. Нужны:

- конкретный плохой artifact: `TC-*`, `ATOM-*`, `GAP-*`, matrix row, writer response, reviewer finding или validator finding;
- источник ожидаемого поведения: ФТ, PDF parity, support artifact, accepted clarification, package notes или reviewer rubric;
- наблюдаемый дефект: что именно writer/reviewer сделал неверно;
- проверяемый критерий, по которому следующий прогон можно признать `pass` или `fail`.

## Источники сигналов

Используй как input для loop:

- `round-N-findings.md` с `severity = error | warning`;
- writer response, который не закрыл finding или закрыл его формально;
- `cycle-state.yaml` со статусом `round-cap-reached`;
- user correction, где пользователь явно показывает неправильный тест-кейс, missing coverage, hallucinated behavior или неверную трассировку;
- `ui-validation-report.md` / `ui-evidence-index.md`, если UI-прогон показывает, что baseline case непригоден к исполнению;
- `evals/runs/*.md` со статусом `fail` или `partial`;
- validator findings, если один и тот же smell повторяется в разных scope.

## Когда создавать eval candidate

Создавай candidate только если выполнено хотя бы одно условие:

- один и тот же defect class повторился в нескольких findings, scope или eval runs;
- дефект блокирует sign-off и уже имеет clear expected output;
- пользователь явно указал дефект как пример неприемлемого качества;
- round cap достигнут из-за качества test design, traceability или expected results;
- validator или reviewer нашел gap в самих agent instructions, а не только в одном FT artifact.

Не создавай eval candidate, если:

- ожидаемое поведение невозможно вывести из источников без догадки;
- проблема относится к одному локальному FT package и должна жить только в `AGENT-NOTES.md`;
- дефект уже покрыт существующим validator check и нужен обычный fix artifact, а не новый eval;
- сигнал является спорным preference без pass/fail критерия.

## Расположение candidate

Новые candidates сохраняй в:

```text
evals/candidates/YYYY-MM-DD-<failure-class>-<short-scope>.md
```

`failure-class` должен быть стабильным и пригодным для группировки, например:

- `unsupported-expected-result`
- `lost-requirement-code`
- `merged-positive-negative`
- `mockup-as-requirement`
- `metadata-value-type-as-tc`
- `action-without-observable-artifact`

## Минимальный формат candidate

```md
# <failure-class>: <short title>

## Metadata

- `candidate_id`:
- `created_at`:
- `source_signal`:
- `affected_skill`:
- `failure_class`:
- `status`: `candidate | accepted-eval | rejected | implemented | superseded`

## Failure Signal

- `bad_artifact`:
- `bad_output_excerpt`:
- `why_it_is_wrong`:
- `source_or_rule_ref`:

## Evidence Bundle

- `ft_package_or_fixture`:
- `review_findings`:
- `traceability_refs`:
- `test_case_refs`:
- `validator_output`:

## Pattern / Recurrence

- `seen_in`:
- `same_failure_shape`:
- `not_noise_because`:

## Eval Target

- `input_fixture`:
- `expected_detection_or_output`:
- `pass_criteria`:
- `fail_criteria`:

## Bounded Improvement Task

- `writable_surfaces`:
- `read_only_context`:
- `out_of_scope`:

## Validation Gates

- `targeted_eval`:
- `regression_suite`:
- `manual_review_needed`:

## Routing Decision

- `decision`:
- `reason`:
- `next_action`:
```

## Bounded task rule

Candidate должен задавать ограниченную задачу для Codex:

- writable surfaces: конкретные `skills/`, `references/`, `scripts/`, `tests/` или `evals/`;
- read-only context: исходные ФТ, support-файлы, previous outputs, reviewer findings, UI evidence;
- validation gates: targeted eval plus relevant regression suite;
- explicit stop condition: что считается достаточным улучшением.

Если исправление требует продуктового решения, уточнения аналитика или доменного поведения вне ФТ, candidate должен идти в `rejected` / `blocked-input`, а не превращаться в prompt rule.

## Связь с review-cycle

`ft-test-case-iteration` отвечает за превращение итогов review-cycle в candidate, если триггеры выше выполнены.

Reviewer не обязан создавать eval candidate на каждое замечание. Его задача - сделать findings достаточно конкретными: указать `review_mode`, `severity`, `category`, `coverage_dimension`, `traceability_ref` / `test_case_id`, evidence и exact required change. Iteration затем группирует повторяемые findings в candidate.

## Связь с eval runs

Когда candidate превращен в реальный eval, сохраняй результат запуска по `eval-run-report-format.md` в `evals/runs/`.

Manual или simulated pass нельзя выдавать за runtime pass. Если runner отсутствует, явно укажи `mode: manual` и residual risk.

## Источник подхода

Подход адаптирует трехчастный контур из статьи OpenAI "Building self-improving tax agents with Codex": expert corrections, product traces, Codex-driven eval-backed iteration. В этом проекте аналогами являются user/reviewer corrections, agent artifacts/traces и bounded eval tasks.
