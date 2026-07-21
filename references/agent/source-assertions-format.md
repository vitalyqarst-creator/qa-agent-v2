# Source-first assertion contract

Этот контракт используется `prepared_compiler_contract_version: 3`. Он переносит проверку смысла требований до writer-а и не позволяет writer/reviewer повторно интерпретировать уже подтверждённую семантику.

## Обязательные артефакты

`workflow-state.yaml/latest_artifacts` должен содержать:

- `source_row_inventory` — полный перечень строк выбранного scope;
- `source_row_extraction_spec` — hash-bound XPath-регионы выбранного XHTML;
- `source_row_baseline` — полный candidate registry этих регионов;
- `source_assertions` — `source-assertions.json` по схеме `version: 4`;
- `source_assertion_review` — независимый `source-assertion-review.json` по схеме `version: 6`;
- `coverage_gaps` — gap artifact, чей path и SHA-256 входят в manifest как
  `coverage_gaps_artifact`.

Рекомендуемые имена в active stage-handoff: `source-assertions.json`,
`source-assertion-review.json`, `prompt.scope-assertions-to-reviewer.md`. Scope
analyzer владеет manifest-ом, независимый reviewer — receipt-ом. Один субъект не
создаёт оба артефакта.

## `source-assertions.json`

Корневые поля: `version`, `scope_slug`, `sources`, `source_rows`, `assertions`,
обязательный массив `clarifications`,
`source_row_extraction_spec_digest`, `source_row_baseline_digest`,
`source_row_candidate_count`, `coverage_gaps_artifact = {path, sha256}`,
опционально `evidence_sources` и `mockups`. Compiler exact-сравнивает
path с `workflow-state/latest_artifacts.coverage_gaps`; любое изменение bytes
делает manifest устаревшим.

Каждый `source` содержит repository-relative POSIX `path` и текущий `sha256`.
`source` — UTF-8 extraction source, в котором дословно находятся
`exact_source_text`; orphan source без assertion chain запрещён.

`source_rows` — обязательный hash-bound registry с точным набором rows из
`source-row-inventory.md`. Каждая row содержит `source_row_id`, `source_path`,
`source_locator`, `bounded_source_text`, `source_context_class`,
`scope_disposition = yes | unclear | no`, nullable `candidate_id` и точные
`requirement_codes`. Для строки выбранного XHTML `candidate_id` обязателен и
ссылается ровно на один deterministic baseline candidate; non-XHTML строка имеет
JSON `null`. Compiler
v3 сравнивает весь registry с inventory по значениям, поэтому перестановка
`SRC-*` ids между реальными строками блокируется как
`source-row-registry-mismatch`. `no` rows не отбрасываются:
их assertions обязаны быть только `not-applicable`. `unclear` row не может
содержать assertion с `execution_readiness = ready`.

Completeness не доказывается сравнением двух co-authored файлов. Compiler заново
выполняет `source-row-extraction-spec.json`, exact-сравнивает полученный candidate
set с `source-row-baseline.json` и требует bijection: каждый selected-XHTML
candidate отображён ровно одной manifest row, без missing/unknown/duplicate.
Manifest digest включает digests spec/baseline и candidate count.
Каноническая схема extraction, enumeration и mapping определена только в
`references/agent/source-row-baseline-format.md`.

Selected scope ограничивает проверяемую функцию, но не разрешает начинать source
inventory с заголовка выбранного раздела. До фиксации manifest-а необходимо
проверить document-global constraints, preamble родительских/выбранного разделов
и cross-referenced constraints. Все применимые строки такого контекста входят в
`source-row-inventory.md` и manifest на тех же правах, что строки внутри раздела.

Compiler также exact-сравнивает manifest registry с SHA-bound таблицей
`source-selection.md` (`path | role | sha256 | manifest_binding`). Закрытое
отображение: `main-ft-xhtml | assertion-source` → `sources`;
`main-ft-docx | semantic-source-of-truth`,
`main-ft-pdf | structural-visual-parity`,
`support | supporting-material` и
`mandatory-package-context | supporting-material` → `evidence_sources`;
`approved-clarification | approved-clarification` → `evidence_sources`;
`mockup | mockup` → `mockups`; `not-used` не попадает в manifest.
`support | assertion-source` запрещён: baseline v1 доказывает полноту
только для одного selected main XHTML; support не может стать exact-text
assertion source до появления generalized multi-source baseline.
Лишний, пропущенный, переименованный или изменившийся path/SHA блокирует compiler.

`evidence_sources` hash-связывает с тем же manifest digest бинарные и
вспомогательные материалы, использованные при независимом semantic review. Каждый
элемент содержит `path`, `sha256` и одну роль:

- `semantic-source-of-truth` — канонический DOCX или другой главный источник;
- `structural-visual-parity` — PDF/иной visual parity source;
- `supporting-material` — support-документ, реально использованный для семантики,
  словаря или oracle.
- `approved-clarification` — UTF-8 Markdown с canonical structured row ответа,
  который разрешён для ready semantics только через typed clarification binding.

Если UTF-8 extraction source не является каноническим source of truth,
`evidence_sources` обязателен. Для FT-пакета DOCX+XHTML+PDF: XHTML регистрируется в
`sources`, DOCX — как `semantic-source-of-truth`, PDF — как
`structural-visual-parity`; использованный support также регистрируется. Изменение
любого такого файла делает receipt stale и блокирует compilation/promotion.

Каждый mockup дополнительно содержит `screen_name` и полный набор используемых
UI-locator-ов.

Каждый assertion содержит:

- стабильные `assertion_id`, `source_row_id`, один `atom_id` и связанные `obligation_ids`;
- `source_path`, точный `locator` и `exact_source_text` из XHTML;
- hash-bound `source_context_class`: `scope-local`,
  `document-global-constraints`, `ancestor-and-section-preamble` или
  `cross-referenced-constraints`; все assertions одной source row имеют один класс;
- опциональный duplicate-free `exact_source_fragments` для дополнительных
  дословных фрагментов той же semantic row, разделённых inline XHTML markup;
- обязательный массив `supporting_source_bindings` для законного cross-row
  evidence, которое не является clause/code provenance; каждый элемент явно
  указывает другую `source_row_id`, роль и точный fragment declared row;
- проверенный `canonical_statement`;
- закрытые классификации `polarity`, `semantic_disposition`, `risk`;
- независимые `execution_readiness = ready | dependency-blocked | not-applicable`
  и `execution_readiness_rationale`;
- раздельные `condition_clauses`, `action_clauses`, `oracle_clauses`;
- точные `requirement_codes`;
- `requirement_code_bindings`: ровно одна typed provenance binding на каждый
  code. Для `xhtml-row` обязательны `source_row_id` и token-bounded
  `exact_source_fragment`, содержащий code; PDF-only code требует exact
  `evidence_source_path` зарегистрированного `structural-visual-parity` source и
  `evidence_locator = page:<positive-integer>`. Validator повторно извлекает
  указанную 1-based PDF page и требует literal token-bounded code именно на ней;
- `clause_evidence_bindings`: минимум одна typed binding на каждый индекс каждой
  condition/action/oracle clause с exact `source_row_id`, совпадающей ролью и
  exact fragment внутри bounded row;
- обязательный массив `clarification_clause_bindings`. Каждый элемент связывает
  один `CLR-*`, точный clause kind/index, `binding_scope`, `source_row_ids`,
  локальные `requirement_codes` и SHA-256 exact answer. Для
  `binding_scope = requirement-code` codes непусты, `source_row_ids = []`,
  локальные codes являются subset clarification и assertion, а union bindings
  точно равен codes clarification. Для `binding_scope = source-context` codes
  обязаны быть `[]`, `source_row_ids` непусты и каждая clause binding называет
  ровно собственную `assertion.source_row_id`; union bindings точно равен row set
  clarification. Обычные kinds `condition | action | oracle` разрешены только
  для `testable` assertion и ссылаются на существующий индекс соответствующего
  clause. Узкое исключение для контекстного ответа —
  `clause_kind = canonical`, `clause_index = 0`: оно разрешено только при
  `binding_scope = source-context` для `not-applicable` assertion с
  `execution_readiness = not-applicable`, пустыми condition/action/oracle,
  пустыми `obligation_ids` и содержательным `disposition_rationale`. Такой
  binding hash-связывает clarification с `canonical_statement`, не создаёт
  исполнимую обязанность и запрещён для `requirement-code`, `testable`,
  `ambiguous` и любого индекса, отличного от `0`;
- обязательный `primary_gap_id`: один `GAP-*` для `ambiguous` и JSON
  `null` для `testable | not-applicable`;
- обязательный duplicate-free `execution_dependency_gap_ids`. Он непуст
  и разрешён только для `semantic_disposition = testable` +
  `execution_readiness = dependency-blocked`; во всех остальных
  комбинациях он обязан быть `[]`.

Каждый execution-dependency GAP в hash-bound `coverage_gaps_artifact` обязан
иметь `Impact: blocking`, `blocks_ready_for_review: yes`, `status: open`
и dedicated поля `execution_assertion_ids`, `execution_atom_ids`,
`execution_obligation_ids`. Их наборы exact-равны всем manifest chains,
которые ссылаются на этот GAP. Общие `affected_*` поля могут
дополнительно описывать более широкий semantic gap, но не
заменяют dedicated execution chain.

`ambiguous` и `not-applicable` assertion дополнительно обязаны
содержать содержательный `disposition_rationale`, объясняющий по
точному source evidence причину неоднозначности или исключения.
Одного enum без rationale недостаточно. `ambiguous` без `primary_gap_id`
запрещён; `testable` и `not-applicable` не могут присвоить себе primary gap.

`polarity`: `positive | negative | neutral`. `semantic_disposition`: `testable | ambiguous | not-applicable`. `risk`: `low | medium | high | critical`.

Testable assertion обязан иметь action, oracle и obligation. Ambiguous
assertion не может заявлять executable obligation и обязан маршрутизировать
неоднозначность через `primary_gap_id`. Not-applicable assertion также не может
заявлять `obligation_ids`: downstream obligation authentication охватывает только
testable obligations.

Минимальная форма:

```json
{
  "version": 4,
  "scope_slug": "scope-slug",
  "source_row_extraction_spec_digest": "<64 hex>",
  "source_row_baseline_digest": "<64 hex>",
  "source_row_candidate_count": 1,
  "coverage_gaps_artifact": {
    "path": "fts/pkg/work/stage-handoffs/01-scope/scope-coverage-gaps.md",
    "sha256": "<64 hex>"
  },
  "sources": [{"path": "fts/pkg/source/main.xhtml", "sha256": "<64 hex>"}],
  "source_rows": [{
    "source_row_id": "SRC-ROW-003",
    "source_path": "fts/pkg/source/main.xhtml",
    "source_locator": "table 4.2 / BSR 3",
    "bounded_source_text": "<полный текст source row>",
    "source_context_class": "document-global-constraints",
    "candidate_id": "SRC-CAND-<24 hex>",
    "scope_disposition": "yes",
    "requirement_codes": ["BSR 3"]
  }],
  "evidence_sources": [
    {
      "path": "fts/pkg/source/main.docx",
      "sha256": "<64 hex>",
      "role": "semantic-source-of-truth"
    },
    {
      "path": "fts/pkg/source/main.pdf",
      "sha256": "<64 hex>",
      "role": "structural-visual-parity"
    }
  ],
  "clarifications": [],
  "assertions": [{
    "assertion_id": "ASSERT-001",
    "source_path": "fts/pkg/source/main.xhtml",
    "source_context_class": "document-global-constraints",
    "locator": "table 4.2 / BSR 3",
    "exact_source_text": "<точный текст строки>",
    "canonical_statement": "<проверенная атомарная семантика>",
    "polarity": "positive",
    "semantic_disposition": "testable",
    "execution_readiness": "ready",
    "execution_readiness_rationale": "none_required",
    "risk": "high",
    "condition_clauses": ["<условие>"],
    "action_clauses": ["<действие пользователя/системы>"],
    "oracle_clauses": ["<наблюдаемый результат>"],
    "requirement_codes": ["BSR 3"],
    "requirement_code_bindings": [{
      "requirement_code": "BSR 3",
      "source_row_id": "SRC-ROW-003",
      "provenance_role": "xhtml-row",
      "exact_source_fragment": "BSR 3. <точный текст строки>",
      "evidence_source_path": null,
      "evidence_locator": null
    }],
    "clause_evidence_bindings": [
      {"clause_kind": "condition", "clause_index": 0, "source_row_id": "SRC-ROW-003", "evidence_role": "condition", "exact_source_fragment": "<точный текст строки>"},
      {"clause_kind": "action", "clause_index": 0, "source_row_id": "SRC-ROW-003", "evidence_role": "action", "exact_source_fragment": "<точный текст строки>"},
      {"clause_kind": "oracle", "clause_index": 0, "source_row_id": "SRC-ROW-003", "evidence_role": "oracle", "exact_source_fragment": "<точный текст строки>"}
    ],
    "source_row_id": "SRC-ROW-003",
    "atom_id": "ATOM-003",
    "obligation_ids": ["OBL-BSR-003"],
    "execution_dependency_gap_ids": [],
    "primary_gap_id": null,
    "supporting_source_bindings": [],
    "clarification_clause_bindings": []
  }],
  "mockups": [{
    "path": "fts/pkg/mockups/screen.png",
    "sha256": "<64 hex>",
    "screen_name": "<видимое название экрана>",
    "locators": ["<только визуально подтверждённые элементы>"]
  }]
}
```

`exact_source_text` нормализуется только по transport whitespace. Исправление
регистра, пунктуации или смысла ради совпадения запрещено. DOCX остаётся source of
truth; exact text берётся из обязательного XHTML, а расхождение с DOCX/PDF идёт в
parity/gap, не скрывается canonical statement-ом.

Literal match не может обрываться внутри Unicode letter/digit token: например,
фрагмент `4 цифр` не совпадает с source text `4 цифры`. Подфрагмент предложения
или ячейки остаётся допустимым, если его границы отделены пробелом, пунктуацией
или границей текста.

`exact_source_text` остаётся обязательным. `exact_source_fragments` используется
только когда одна semantic row представлена несколькими contiguous text
fragments из-за inline markup; primary text и все такие fragments должны
находиться внутри `bounded_source_text` primary row. Глобальный поиск по всему
файлу запрещён. Cross-row evidence для condition/action/oracle и requirement
code задаётся только через typed clause/code bindings. Прочее разрешённое
semantic evidence задаётся через
`supporting_source_bindings = {source_row_id, evidence_role,
exact_source_fragment}`; fragment проверяется внутри bounded text declared row.
Допустимые роли: `subject`, `property`, `applicability`, `constraint`,
`cross-reference`, `definition`, `polarity`. Роли `condition`, `action`,
`oracle` и `requirement-code` запрещены здесь: их единственный источник истины —
typed clause/code bindings. Assertion `requirement_codes` должен точно, а не как
subset, совпадать с code set `requirement_code_bindings`.

### Целостность registry coverage gaps

Каждый `primary_gap_id` обязан совпадать с отдельным `GAP-*` heading в hash-bound
`coverage_gaps_artifact`; такой GAP обязан иметь `status = open`. Canonical поля
`affected_assertion_id` и `affected_atom_id` содержат duplicate-free списки через `;`.
Все assertions, указавшие GAP как primary, обязаны входить в
`affected_assertion_id`, а множество `affected_atom_id` обязано точно совпадать с
ATOM-владельцами всего declared `affected_assertion_id`. Семантический gap может
затрагивать дополнительные assertions, поэтому primary membership проверяется как
subset, а не как ошибочное равенство только primary assertions. Для primary-only GAP
не требуются execution-only поля, `Impact: blocking` или
`blocks_ready_for_review: yes`; эти требования действуют только для фактической
`execution_dependency_gap_ids` chain.

Каждый GAP heading обязан иметь typed binding как primary gap, execution dependency,
resolved approved clarification либо canonical непустую affected chain. Последний
вариант сохраняет semantic constraint gap для testable assertion, даже если он не
является primary или execution dependency: его `affected_assertion_id` должен
ссылаться только на manifest assertions, а `affected_atom_id` — точно совпадать с их
ATOM-владельцами. Иной heading считается `orphan-coverage-gap` и блокирует manifest;
prose или один `status` binding не заменяют typed chain.

## Approved clarifications

Для каждого зарегистрированного `approved-clarification` evidence path множество
canonical строк текущего `scope_slug` с `response_status = answered` и approved
`response_type` обязано точно совпадать с `clarifications[]` этого path. Принятый
ответ нельзя молча оставить незарегистрированным; typed record, clause bindings и
точный code/row union остаются обязательными. Строки другого scope и ответы с
неapproved type не становятся ready semantics и в это множество не входят.

`clarifications[]` — typed registry, а не копия prose. Каждая запись содержит
`clarification_id`, `gap_id`, `scope_slug`, `binding_scope`, `source_row_ids`,
`requirement_codes`, фактический
`authority`, `response_status`, `response_type`, `answered_at`, `exact_answer`,
`exact_answer_sha256`, `evidence_source_path` и `evidence_source_sha256`.

Ready semantics разрешены только для `response_status = answered` и точной пары
`user/user-confirmed`, `analyst/analyst-confirmed` или
`product-owner/product-confirmed`. Нельзя записывать пользователя как analyst
или product owner. `working-assumption`, `rejected`, `superseded`, `unanswered`
и `not-provided` никогда не bind-ят ready assertion.

Поведенческое уточнение использует только `binding_scope = requirement-code`:
`requirement_codes` обязаны быть непустыми, а `source_row_ids` — пустыми. Ответ о
section/main-form context без буквенно-цифрового кода может использовать
`binding_scope = source-context`, но только с `requirement_codes = []` и непустым
duplicate-free набором hash-bound `source_row_ids`. Каждая такая row обязана
существовать в manifest, иметь `scope_disposition = yes` и совпадать с row
assertion, чью clause либо узкий `canonical[0]` slot уточняет ответ. Поэтому
context answer нельзя приписать
чужому BSR, ignored/unclear row или orphan context. Exact answer digest и полный
set-equality clause bindings остаются обязательными.

Backward-compatible decoder старого v4 payload без новых полей допускает только
непустые legacy `requirement_codes` как `binding_scope = requirement-code` с
`source_row_ids = []`. `source-context` не infer-ится; текущая serialization
всегда пишет оба поля.

Evidence path обязан быть зарегистрирован в source-selection и manifest с ролью
`approved-clarification`. Hash-bound Markdown должен содержать canonical table
из `scope-clarification-requests-format.md`; structured row обязана дословно
совпасть с typed record. Связанный coverage gap остаётся трассируемым, но имеет
ровно `status = resolved`, `resolution = approved-clarification:<CLR-ID>` и не
содержит активную execution chain. Только такой manifest-validated exact gap id
исключается из `gap-without-obligation`; он не становится `PreparedGap` и не
блокирует release. Другой orphan, включая prose-only resolved gap, блокируется.

Каждый clarification обязан иметь хотя бы один clause-level либо `canonical[0]`
binding, и orphan
`approved-clarification` source запрещён. Изменение answer или любого provenance
field меняет manifest digest и требует новый независимый receipt. Compact
writer/reviewer projection включает только выбранные CLR records, но сохраняет
id, authority, exact answer, answer digest и evidence digest без пересказа.

Manifest v3 только диагностический. Миграция v3→v4 допустима при явном
подтверждении отсутствия влияющих clarifications: она создаёт пустые
clarification arrays, не синтезирует approvals и требует нового review v6.
Иначе нужна semantic rematerialization.

Обязательные правила построения condition/action/oracle вынесены в
`source-assertion-semantic-rule-card.md`; source analyzer и независимый reviewer
применяют одну карточку, не дублируя её в prompts.

## Независимый review receipt

Receipt v6 фиксирует `manifest_digest`, включая hash-bound
`evidence_sources`, решение `accepted | changes-required`, ровно один review для
каждого assertion, обязательный `source_inventory_review` и
`scope_boundary_review`. `source_inventory_review` hash-связывает exact extraction
spec/baseline digests, candidate count и mapped selected-XHTML row count;
`accepted` требует `verdict = verified`. Per-assertion review
содержит `assertion_id`, `approved_polarity`,
`approved_semantic_disposition`, `approved_execution_readiness`, `approved_risk`,
`dimension_verdicts`, `verdict`,
`required_change`, `note`.

`dimension_verdicts` — JSON object с ровно тринадцатью фиксированными
ключами:

- `source-binding`;
- `canonical-statement`;
- `requirement-codes`;
- `polarity`;
- `semantic-disposition`;
- `risk`;
- `condition`;
- `action`;
- `oracle`;
- `gap-routing`;
- `execution-readiness`;
- `execution-dependencies`;
- `clarification-provenance`.

Каждое значение равно `verified | incorrect`. Верхний `verdict`
вычисляется из dimensions: `incorrect`, если хотя бы одна dimension
incorrect, иначе `verified`. Для verified review `required_change` должен
быть ровно `none_required`; incorrect review требует содержательный
`required_change`.

Поля `approved_polarity`, `approved_semantic_disposition`,
`approved_execution_readiness` и `approved_risk`
подтверждают текущее manifest value только когда соответствующая
dimension равна `verified`. Если classification dimension равна
`incorrect`, reviewer обязан записать в `approved_*` другое допустимое
предлагаемое значение. Так `changes-required` не заставляет reviewer-а
эхом повторять ошибочную классификацию manifest-а.

`scope_boundary_review` содержит:

- `verdict = verified | incorrect`;
- duplicate-free `checked_context_classes`, причём набор должен быть ровно
  `document-global-constraints`, `ancestor-and-section-preamble`,
  `cross-referenced-constraints`;
- duplicate-free `reviewed_manifest_contexts` — typed entries
  `{context_class, source_row_id}`; набор обязан точно перечислять ВСЕ manifest
  rows трёх boundary classes, включая `scope_disposition = no` и all-N/A rows;
- `excluded_contexts` — явные source-bound исключения с `context_class`,
  зарегистрированными `source_path`/`source_sha256`, точными `source_locator` и
  `exact_source_text`, а также содержательной `reason`;
- `required_change`: ровно `none_required` для `verified`, содержательное
  исправление для `incorrect`;
- содержательную `note` о проверке границ.

Accepted receipt требует `scope_boundary_review.verdict = verified`. Exclusion
никогда не заменяет manifest row и не уменьшает exact
`reviewed_manifest_contexts`: он допустим только для source-bound контекста вне
manifest registry. Если boundary class не имеет ни одной manifest row, reviewer
обязан записать хотя бы одно такое реальное exclusion с обоснованием. Один
`(source_path, canonical source_locator)` нельзя
повторно использовать как exclusion для разных context classes. Пустой
checkbox-style attestation отклоняется.

Runnable identity — `bounded-source-first-assertions-v4` /
`SOURCE-ASSERTIONS-V4`. Manifest v1/v2/v3 и receipts v1-v5 остаются immutable
diagnostic evidence; loader возвращает
`legacy-manifest-requires-rematerialization` или
`legacy-review-receipt-requires-rereview`. Кроме описанной выше v3→v4 миграции,
автоматическая миграция запрещена; legacy identity отклоняется fail-closed.

Компиляция разрешена только при `accepted`, полном множестве
assertion-ов, verified `source_inventory_review`, всех per-assertion
verdict=`verified`, всех тринадцати
dimension verdict=`verified`, точном совпадении polarity, semantic disposition,
risk и digest текущего manifest, а также при валидном verified
`scope_boundary_review`.

`execution_readiness` не является semantic gap. `dependency-blocked` требует
содержательного rationale; остальные значения требуют
`execution_readiness_rationale = none_required`. Compiler v3 fail-closed
останавливает `release` с `source-execution-dependency-blocked`. Только явный
`draft-with-blocking-gaps` компилирует ready subset: исключает точные OBL/ATOM
dependency-blocked assertions, переносит их полный typed registry в package v9
`release_status` и завершает принятый reviewer-ом цикл как unsigned
`blocked-input/blocked-execution-dependencies`. Если ready testable assertion не
осталось, compiler останавливается с `draft-no-ready-execution-assertions` без
writer/reviewer. Dependency нельзя превращать в semantic coverage gap.

`accepted` подтверждает source model, но не означает release eligibility и не
закрывает сохранённые blocking gaps. Канонические режимы compiler-а `release`
(default) и `draft-with-blocking-gaps` определены в
`prepared-compiler-input-contract.md`.

Reviewer проверяет source model напрямую, а не через ledger или writer plan:

- границы проверены от document-global/ancestor context до выбранного раздела,
  а применимые общие ограничения не потеряны и исключения обоснованы;
- строка не потеряна и не объединена с независимым поведением;
- positive/negative polarity соответствует смыслу источника;
- `testable | ambiguous | not-applicable` обоснован источником;
- condition/action/oracle не подменяют друг друга;
- broad gap не скрывает несколько независимых проверяемых dimensions;
- mockup locator существует визуально, но не превращён в бизнес-правило.

Receipt хранит полные per-assertion reviews. В immutable `source-evidence.md`
встраиваются полный bounded manifest и полный receipt; один HTML marker не является
доказательством source-first contract.

## Проверяемые гарантии

Compiler v3 детерминированно проверяет:

- SHA-256 и наличие точного source text с нормализацией только transport-whitespace;
- полноту bounded source-row inventory;
- повторное deterministic extraction и bijective candidate→SourceRow mapping;
- exact source-selection→manifest mapping по path/role/SHA;
- непрерывную цепочку source row → assertion → ATOM → OBL;
- exact typed columns `source_row_id` и `requirement_codes` в каждой ATOM/OBL
  row без free-text scan и prefix-collisions (`GSR 1` не равно `GSR 10`);
- равенство `primary_gap_id` каждого `ambiguous` assertion ровно одному
  фактическому non-constraint GAP в его ATOM/OBL chain; `constraint_gap_ids`
  допустим только для testable atom;
- неизменность canonical statement, requirement codes и polarity receipt;
- exact `source_property_id` lineage across ATOM→OBL and fail-closed rejection
  when a positive reviewed assertion is mapped to explicitly negative typed
  obligation/design classes; free-text polarity guessing is not used;
- соответствие semantic disposition статусу coverage;
- exact 100% completeness independently accepted testable assertion → ATOM →
  covered OBL set, а также descriptive obligation/source-assertion determinacy
  ratios и запрет broad/high-risk nonblocking gaps;
- явную blocking-классификацию каждого gap: compiler v3 не
  использует default `blocking: false`; в default `release` primary blocking
  gap блокирует и fast, и standard package; явный
  `draft-with-blocking-gaps` может сохранить только primary blocking gaps при
  наличии хотя бы одного testable obligation; blocking constraint gap всегда
  запрещён, а broad/nonblocking/high-risk guardrails остаются fail-closed;
- freshness mockup-а и используемые UI locator-ы;
- включение bounded source basis в immutable prepared package.

Compiler не доказывает семантическую эквивалентность русского текста. Это делает отдельный source-first review один раз; последующие стадии проверяют digest и используют утверждённые condition/action/oracle без новой интерпретации.

Coverage accounting сохраняет obligation metrics и отдельно считает
одну coverage unit на каждый reviewed source assertion/ATOM. В обоих
denominator входят `testable + gap + unclear`; `not-applicable` исключается.
Эти ratios описывают определённость source model и не являются promotion floor:
иначе переклассификация testable↔gap могла бы оптимизировать число вместо
качества. Release gate требует exact 100% покрытия всех независимо принятых
testable assertions/obligations. Critical ratio остаётся `1.00`. Разбиение
одного covered assertion на много `OBL-*` не повышает качество. Broad primary gaps,
high/critical nonblocking gaps, testable-to-gap regression и необъяснённый новый gap
блокируют compilation. Любое изменение testable↔ambiguous меняет manifest digest
и требует новый независимый receipt. Узкий low-risk gap допустим только с точным
subject и accepted-risk evidence; broad-gap finding не waivable.

## Reviewer и promotion

Prepared reviewer сначала проверяет source basis → obligation model, затем test
cases. Для source-first package используется reviewer contract v4: reviewer
возвращает точные hashes, один компактный verdict для каждого obligation и один
review для каждого routed cross-cutting dimension. Полный assertion receipt выше
остаётся отдельным pre-compiler доказательством и не заменяется TC-review
receipt-ом.

Production promotion запрещён для legacy package без `SOURCE-ASSERTIONS-V4`, даже если старые structure/traceability gates прошли.
Accepted source assertion receipt также не разрешает promotion, пока хотя бы
один source gap остаётся blocking. Execution-dependency registry всегда делает
package unsigned и блокирует promotion отдельным
`PROMO-BLOCKED-EXECUTION-DEPENDENCIES`.
