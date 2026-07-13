# Stop Gate After V5 Live

## Decision

`STOP — V5 live quota consumed`

## Reason

Единственный writer вернул transport-capacity blocker до materialization. Повтор с тем же package и mode нарушит pre-live authorization и с высокой вероятностью повторно потратит тот же входной контекст.

## Reopen conditions

- новый immutable V6 package/cycle;
- deterministic output-capacity preflight;
- alternative writer transport covered by focused bad/corrected evals and full regression;
- proof that shards/records preserve exact `OBL -> ATOM -> TC` mapping and merge order;
- новый checkpoint и отдельная live authorization.
