# Table Writer Runtime Checklist

Compact table-writer runtime only. Deep examples, review rubrics and historical canary notes stay outside default table writing.

| runtime need | required action | deep reference when needed |
|---|---|---|
| Row-level source parity | Preserve every in-scope or unclear source row before normalization. | `references/agent/source-row-inventory-format.md` |
| Source normalization | Split rows into one semantic property per `source_property_id`; do not merge different property classes. | `references/agent/source-table-normalization-format.md` |
| Dictionary or fixed list | Extract allowed values before TC writing; unresolved active values become `GAP-*` / `unclear`. | `references/agent/dictionary-inventory-format.md` |
| Design decision | Map each executable source property to one TC, existing TC, scenario-only rationale or explicit gap. | `references/agent/test-design-decision-table-format.md` |
| Package plan | Keep package boundaries, TC ids and coverage decisions consistent before final TC write. | `references/agent/package-test-design-plan-format.md` |
| Quality gate | Use compact rule cards and scoped validator output before reviewer handoff; load deep table/debug references only for failed or unclear classes. | `references/agent/deep-reference-loading-policy.md` |

Default table writer must not load full reviewer rubrics, style examples, historical canary analysis or all optional coverage metric templates. Use an explicit deep/debug scenario when those details are needed.
