# Source-To-Package Fidelity Format

Этот контракт фиксирует только высокорисковые source statements, которые нельзя терять или конкретизировать при проекции `source -> ATOM -> OBL -> design plan -> prepared package`. Он не заменяет semantic review и не пытается доказать эквивалентность всего текста ФТ.

## Когда создавать

Создай `source-to-package-fidelity.json`, если подтвержденный scope содержит хотя бы один из случаев:

- буквальный UI-текст, сообщение, подпись или другой source literal, который является наблюдаемым oracle;
- буквальный текст, который используется только как locator и поэтому не должен ошибочно становиться oracle;
- величину с неоднозначной единицей, для которой downstream может выдумать точное преобразование, например `МБ -> байты`;
- явно подтвержденную source-backed policy такого преобразования.

Путь зарегистрируй как `latest_artifacts.source_to_package_fidelity`. Для legacy scope без таких рисков artifact необязателен. Наличие artifact включает deterministic compiler gate.

## JSON Schema V1

```json
{
  "version": 1,
  "scope_slug": "questionnaire-upload-transfer-v7",
  "bindings": [
    {
      "binding_id": "FID-QUT-001",
      "binding_kind": "literal",
      "source_ref": "BSR 206; table 6 row 81",
      "source_text": "Буквальный текст из ФТ",
      "atom_id": "ATOM-QUT-001",
      "obligation_id": "OBL-QUT-001",
      "handling": "preserve",
      "required_targets": [
        "atomic_statement",
        "required_behavior",
        "single_expected_behavior"
      ]
    }
  ]
}
```

Общие правила:

- `version` равен `1`;
- `scope_slug` совпадает с `workflow-state.yaml`;
- `bindings` непустой;
- `binding_id` уникален и имеет формат `FID-*`;
- `atom_id` и `obligation_id` существуют, причем obligation ссылается именно на этот atom;
- `source_ref` и `source_text` непустые;
- допустимые `required_targets`: `atomic_statement`, `required_behavior`, `single_expected_behavior`.

## Literal Binding

`binding_kind = literal` поддерживает два решения:

- `handling = preserve`: `source_text` буквально присутствует во всех `required_targets`;
- `handling = locator-only`: `required_targets` пуст, а `decision_reason` объясняет, почему literal является locator, но не oracle.

`locator-only` нельзя использовать для видимого ожидаемого текста только ради уменьшения prepared package.

## Unit Binding

`binding_kind = unit` дополнительно требует положительный integer `unit_value` и непустой `unit_symbol`. Допустимые решения:

- `coverage-gap`: точная boundary fixture не определена; `gap_id` существует, atom и obligation имеют status `gap` или `unclear` и ссылаются на тот же gap;
- `source-unit-only`: тестируемое правило и fixture остаются в исходной единице без точного byte conversion;
- `decimal-bytes`: преобразование разрешено только с непустым `policy_source_ref`; integer `byte_offset` задает boundary offset относительно `unit_value * 1 000 000`;
- `binary-bytes`: преобразование разрешено только с непустым `policy_source_ref`; integer `byte_offset` задает boundary offset относительно `unit_value * 1 048 576`.

Для `coverage-gap` и `source-unit-only` связанные atom, obligation и plan rows не должны содержать точное значение в `байт` / `bytes`. `source_text` должен сохраняться во всех `required_targets`.

Для byte-conversion handling каждый exact byte value в связанных targets должен совпадать с вычисленным значением `unit_value * base + byte_offset`; отсутствие exact byte value или несовпадение блокируется как `source-fidelity-byte-conversion-mismatch`.

Если точная граница неоднозначна, сохрани отдельное source obligation как gap. Негативный oversized scenario можно оставить testable в исходной единице только с fixture, которая гарантированно превышает лимит при обеих рассматриваемых конвенциях; это не подтверждает точную boundary convention.

## Gate Result

Prepared compiler:

- блокирует потерю literal как `source-fidelity-literal-missing`;
- блокирует byte conversion без policy как `source-fidelity-unit-conversion-without-policy`;
- блокирует несогласованный unit gap как `source-fidelity-unit-gap-mismatch`;
- блокирует несовпадение policy arithmetic как `source-fidelity-byte-conversion-mismatch`;
- включает нормализованные bindings в `source-evidence.md`, поэтому они входят в immutable package fingerprint.

Изменение binding, handling, policy или decision reason требует нового package id/output root; существующий prepared package не перезаписывается.
