# Deterministic-first source-qualified iteration

Этот reference задаёт короткий production-маршрут `ft-test-case-iteration` для
уже квалифицированного bounded scope. Историческое имя instruction scenario —
`iteration.lean_v2`; публичная точка запуска — `ft-agent run`.

Маршрут не является benchmark. Он не передаёт reviewer старые тест-кейсы,
benchmark configs, результаты прошлых попыток и произвольные пути из командной
строки.

## Граница ответственности

До запуска должны существовать:

- package-local `scope-registry.json` с выбранным scope, структурной XHTML-
  границей, полным набором источников и стабильным `tc_prefix`;
- DOCX как source of truth, XHTML как обязательный машиночитаемый источник и
  PDF, если он объявлен;
- source evidence со source-assertion manifest v4 и независимым accepted review
  receipt на точный digest, а также immutable semantic-design compiler
  projection со ссылками и хэшами исходных semantic artifacts;
- compiler-v3 obligations;
- accepted semantic projection, из которой runner сам строит маленький design
  context.

Если любого входа нет или он stale, заверши попытку как `blocked-input`. Повторная
квалификация выполняется вне этого bundle в development/qualification среде;
нельзя заменять её ручным пересказом требований или брать старый TC suite как
источник.

## Единственный публичный запуск

```powershell
ft-agent run `
  --config fts/<ft-slug>/work/<handoff>/run-config.json `
  --output-dir fts/<ft-slug>/work/iterations/<new-attempt-id>
```

`run-config.json` имеет закрытую схему:

```json
{
  "schema_version": 2,
  "registry": "fts/example-ft/scope-registry.json",
  "ft_root": "fts/example-ft",
  "scope": "confirmed-scope",
  "source_evidence": "fts/example-ft/work/handoff-001/source-evidence.md",
  "obligations": "fts/example-ft/work/handoff-001/obligations.json"
}
```

Schema v1 с явным `derivations` остаётся только compatibility API для старых
внутренних handoff. Новые production-конфиги используют schema v2.

Config принимает ровно шесть полей из примера. Он не принимает `ft_slug`, design
context, `tc_prefix`, source/canonical allowlists, output status, promotion target
или готовый файл derivations. Slug и prefix выводятся из `ft_root` и registry;
защищаемые sources — из accepted manifest и registry; canonical baseline — из
всех `test-cases/**/*.md` выбранного FT-пакета. Typed derivations и design
context автоматически строятся из принятого manifest, obligations и hash-bound
semantic projection и сохраняются внутри immutable attempt.

## Последовательность

Runner в одном процессе и одном immutable attempt:

1. загружает закрытый config и фиксирует хэши всех run inputs;
2. резолвит только выбранный scope, чтобы дефект другого scope не блокировал
   текущий;
3. заново компилирует XHTML boundary и candidate set;
4. требует точного равенства registry и manifest по path, bucket, role и
   актуальному SHA-256, включая DOCX/XHTML/PDF/support/mockups;
5. проверяет accepted source-review receipt и obligations, затем автоматически
   строит и hash-bind-ит typed derivations из semantic projection;
6. строит и полностью валидирует coverage graph;
7. формирует все test-case designs и весь Markdown детерминированно, без
   model-call;
8. запускает production gate;
9. вызывает ровно одного независимого reviewer на компактной source-first
   projection;
10. повторно проверяет run inputs, source/canonical hashes и пишет terminal
    summary.

Scopes выполняются последовательно. Внутреннего retry и продолжения испорченной
попытки нет; повтор всегда получает новый output directory.

## Model boundary

Единственный model stage — reviewer. Он запускается в свежем tool-free process
после полного suite gate, получает graph-bound projection и draft digest, не
редактирует результат и не может принять warning или finding как `accepted`.
Runner обязан зафиксировать ровно один reviewer request/receipt; отсутствие или
повторный вызов блокирует acceptance.

Reviewer проверяет только переданные condition/action/fixture/state axes и не
требует гипотетических состояний. Если before/after states явно присутствуют в
проекции, пропущенное состояние остаётся finding. Исполнимый кейс получает
`covered`; честно помеченный calibration-кандидат — `calibration-pending` после
проверки трассировки, calibration question и отсутствия придуманного oracle.
Одна лишь неисполняемость calibration-кандидата не является finding.

Недоступный UI oracle не превращается в догадку. Calibration candidate остаётся
в том же suite, но явно помечается как неисполняемый до UI-калибровки.

## Immutable и publication boundary

- `output-dir` обязан быть новым child path под `fts/<ft-slug>/work/`;
- модель работает без hard application timeout по умолчанию;
- canonical, workflow state и source files не изменяются;
- успешный terminal status — `accepted-shadow` либо
  `accepted-with-calibration-pending`, не `signed-off`;
- `accepted-with-calibration-pending` всегда имеет `promotion_eligible=false`
  и `non_promotable_reason=calibration-pending`;
- promotion не входит в `ft-agent run`.

Promotion выполняется вне этого downstream bundle отдельной development-
транзакцией только для неизменившегося
`accepted-shadow` без pending calibration: повторно проверяются graph, production gate, reviewer receipt,
полный canonical baseline и source hashes. Ручная правка lifecycle или прямая
запись в canonical запрещены.

## Результаты и измерение

В корне attempt сохраняются:

- `scope-compilation/`;
- `bindings/accepted-coverage-contract.json`;
- `run-input-receipt.json`;
- `graph/coverage-graph.json`;
- `context/design-context.json`;
- `iteration/` с prompts, receipts, shadow draft, gate и review;
- `terminal-summary.json`;
- отдельный diagnostic для terminal failure.

Summary охватывает загрузку config, scope compilation, source binding, graph,
design context, единственный reviewer stage и final reconciliation. Для reviewer
указывай wall time, attempts, input/output artifact count и bytes, а токены —
только как неотрицательные целые либо `unavailable`. Токены root orchestration
всегда `unavailable`, никогда не `0`.
