# Формат независимого результата review practical v0.9

```json
{
  "review_manifest_sha256": "<sha256 manifest>",
  "scope_id": "<scope id from manifest>",
  "scope_slug": "<scope slug from manifest>",
  "review_mode": "matrix",
  "execution_surface": "codex-thread",
  "reviewer_thread_id": "<другая верхнеуровневая Codex-сессия>",
  "review_session_attestation_sha256": "<sha256 controller-owned attestation>",
  "independent_obligations": [
    {
      "source_anchor": "Раздел 9.1, строка «Партнеры»",
      "statement": "В меню доступен пункт «Партнеры».",
      "obligation_ids": ["OBL-001"]
    }
  ],
  "verdict": "approved",
  "findings": []
}
```

`reviewer_thread_id` — устойчивый UUID другой верхнеуровневой Codex-сессии;
он должен отличаться от `controller_thread_id` из manifest. Каждый элемент
`independent_obligations` содержит восстановленные reviewer-ом `source_anchor`
и `statement`, а также связанные `obligation_ids`. Все `obligation_ids` в
сумме должны в точности покрывать `OBL-*` из зафиксированного
`scope-obligations.json`.

Перед передачей результата controller создаёт immutable
`review-session-attestation.json` штатным скриптом. Attestation связывает
фактический ID reviewer-а с теми же нормализованными `repo_root` и
`ft_package_root`, что и manifest. Reviewer получает его как
часть snapshot и переносит его SHA-256 в
`review_session_attestation_sha256`. Это подтверждает, что ID reviewer-а
зафиксирован controller-ом после создания отдельной задачи, а не только
заявлен самим reviewer-ом. Локальный контракт не подменяет API задач и не
заявляет криптографическое доказательство создания сессии: при отсутствии
controller-owned attestation финализация честно блокируется.

Для scope, у которого manifest содержит `reviewer_receipt_contract`, reviewer
использует компактный вектор вместо массива `independent_obligations`:

```json
{
  "independent_obligation_vector_digest": "<active_obligation_ids_sha256 из manifest>",
  "independent_obligation_vector": [
    {
      "obligation_id": "OBL-001",
      "source_anchor": "Раздел 9.1, строка «Партнеры»",
      "statement": "В меню доступен пункт «Партнеры».",
      "verdict": "covered"
    }
  ]
}
```

Вектор содержит ровно одну запись на каждый `OBL-*` из manifest. `source_anchor`
и `statement` reviewer формулирует самостоятельно после чтения snapshot;
`verdict` — `covered`, `gap` или `blocked`. При `approved` все значения должны
быть `covered`. Digest связывает вектор с immutable набором OBL, но не заменяет
построчную проверку покрытия.

Сначала reviewer читает источники и формирует `independent_obligations`; затем сопоставляет их с matrix и, при `review_mode: test-cases`, с TC. Нельзя использовать transcript writer-а, self-check или изменения matrix/TC как вход первичной оценки.

Для каждого открытого `ui-calibration` reviewer отдельно проверяет связанные
изображения в самом ФТ, PDF и visual-only inputs. Если они определяют
идентичность, подпись или расположение контрола, reviewer фиксирует finding:
эти данные должны быть `visual_binding` соответствующего `OBL-*`, а не
калибровкой. Если gap оправдан, reviewer проверяет непустой
`visual_evidence_check` и то, что остаточная неопределённость относится только
к runtime-поведению либо конфликту источников.

Reviewer не считает дефектом повторное использование одного стабильного
fixture или DaData-профиля в однотипных проверках. Но он фиксирует finding,
если в «Тестовые данные» копируется полный профиль, а его отдельные literals
не участвуют в шагах, итоговом ожидаемом результате и не нужны для
сохранения/перехода. В таком случае writer оставляет в TC только используемые
конкретные значения, а не заменяет их ссылкой на fixture.
Отдельно проверь, что `CTX-*` не подменяет пользовательский вход на экран в
шаге: при неизвестной навигации открытый экран указывается в нейтральном
предусловии. В canonical TC не должно быть `SETUP-*`, URL, маршрута входа,
конкретной учётной записи, логина, пароля, токена или cookie; они относятся к
волатильной конфигурации среды. В matrix допустим только нейтральный
идентификатор предпосылки. Для каждого DaData-сценария потребуй сохранённый
`FX-DADATA-*` с используемыми literals, совпадающими с verified receipt и
response snapshot, либо точные свойства отсутствующего ответа и явный способ
его подготовки. «Известная организация» или
«подготовить организацию» без этих данных — blocking finding.
Не допускай предпосылку «получен список DaData», когда сам TC вводит запрос
или выбирает подсказку: это дублирует trigger-state. Проверяй русский язык
runtime-полей и отклоняй английские служебные формулировки наподобие
`frozen profile`.

Проверь статус и ограничения исполнения раздельно. Если primary статус
правильно выведен из бизнес-предпосылок, но остаётся другое существенное
бизнес-ограничение, finding не требует сменить primary статус: он требует поле
«Ограничения исполнения» с русским пояснением. Волатильный доступ к среде с
`availability_scope: environment-access` не является ограничением исполнения.
При одном точном
результате отказа для нескольких source-defined классов невалидного ввода
проверь, что этот результат присутствует в matrix и TC каждого класса, а не
только одного примера.

При восстановлении нельзя упрощать исходную норму до более широкого утверждения:
обязательно сохраняй контекст выполнения (например, создание и
редактирование), кванторы, граничные значения, условия и исключения. Если
разные контексты или классы входных данных дают самостоятельные проверяемые
потоки, они должны быть разложены на разные `OBL-*`/matrix rows/TC.

Reviewer сам проверяет решения `CON-*` в разделе консолидации matrix, а не
доверяет prose writer-а:
у параметризованной группы совпадают проверяемый элемент, домен проверки,
способ взаимодействия, контекст, тип и статус исполнения; `parameterization_basis`
описывает только допустимый вид параметра. Для `поля одного составного
результата` разные поля допустимы лишь при одном механизме, action и primary
oracle, полном `field_inventory`, `composite_result` и таблице всех полей в
TC. Разные validation, UI-уровни, сохранение, editability и ручной ввод как
самостоятельные механики не объединяются. Если manifest содержит этот contract, result включает
`scenario_consolidation_review` с `checked=true`, `decision_ids` из manifest,
`uncategorized_candidate_count` и `method`. При `approved` счётчик равен нулю;
неучтённая группа — отдельный finding, без изменения workflow reviewer-ом.

`blocked-observability` — допустимый статус исполнения для представимого
утверждения ФТ. Finding о том, что matrix/TC должен использовать этот статус,
не объявляет требование external blocker и не должен автоматически иметь
`blocking: true`; блокирующим остаётся только отсутствие представимого
source-backed покрытия или противоречие источников.

`findings` содержит объекты с полями `id`, `title`, `details`,
`source_anchor`, `artifact_anchor`, `category`, `severity`,
`blocking` и `remediation_owner`; у blocking finding обязательно
`blocking_reason`. Все содержательные поля формулируются по-русски.
`remediation_owner` определяет исполнителя исправления, но не меняет природы
finding: blocking-дефекты категорий `coverage`, `expected-result`,
`test-design`, `traceability`, `execution-readiness` и иные предметные
замечания всегда проходят controller triage и могут быть исправлены только в
единственной writer-доработке своей фазы. Значения `controller` и `validator`
допустимы без расходования writer budget только для процессных категорий
`review-integrity`, `source-integrity`, `transport`, `validator` или `tooling`.
Это правило действует для `controller-triage-v2` и `controller-triage-v3`.
`controller-triage-v1` поддерживается только для проверки уже финализированной
истории; не назначай его новым scope и не переписывай под более новый контракт
его immutable triage-записи.

Для `controller-triage-v3` каждый блокирующий содержательный finding
дополнительно содержит `remediation_closure`:

```json
{
  "basis": "Та же обязательная проверка после заполнения остальных обязательных полей в потоке создания и редактирования.",
  "scenario_ids": ["SCN-025", "SCN-026"],
  "obligation_ids": ["OBL-013"]
}
```

`scenario_ids` и `obligation_ids` могут быть пустыми только по отдельности,
но не одновременно. Reviewer перечисляет полный известный охват первопричины,
а не выборочные примеры. Writer использует его как минимальный набор и
расширяет по matrix все однотипные сценарии с тем же правилом, действием,
объектом и контекстом. Это не создаёт новый цикл доработки: closure проверяется
в рамках единственной разрешённой writer revision.
Если finding требует изменить статус исполнения, он дополнительно содержит
`status_assertion`:

```json
{
  "scenario_ids": ["SCN-..."],
  "required_status": "needs-test-data"
}
```

Эта структура нужна только для проверяемого controller triage: controller
сверяет `required_status` с фактической полной цепочкой `SETUP-*`.
Не используй её для общих замечаний о качестве текста или покрытии.

Reviewer возвращает этот объект как один raw JSON submission. Controller не
исправляет и не переформулирует его поля, в том числе source anchors, а
сохраняет byte-for-byte через `capture_practical_review_result.py`. Ошибка
кодировки исправляется только новым submission reviewer-а или исправлением
validator-а; она не даёт controller-у права нормализовать evidence.

Поле `verdict` допускает только `approved`, `changes-required` или
`blocked-input`. Значения `rejected`, `failed`, `blocked` и локальные синонимы
недопустимы: такой raw response не финализируется и не расходует revision
budget. При содержательных замечаниях без внешнего blocker reviewer выбирает
`changes-required`.

Raw submission ограничен размером, указанным в `reviewer_receipt_contract`
manifest (по умолчанию не более 24 KiB). Перед отправкой reviewer сохраняет
тот же raw JSON во временный UTF-8 файл и запускает
`python scripts/validate_practical_review_submission.py --manifest <manifest> --submission <временный-json>`.
Controller принимает только результат, прошедший этот preflight. Если первый ответ не проходит этот
контракт, controller не просит reviewer-а «сжать» уже вынесенный verdict и не
переписывает receipt: он фиксирует невалидный dispatch и при необходимости
запускает новый независимый review по тому же immutable snapshot.

После `changes-required` controller сам выполняет triage raw findings, затем
немедленно финализирует этот же неизменённый raw verdict до любой writer-
доработки. Reviewer не определяет расход revision budget, не меняет
`workflow-state.json` и не помечает свой verdict как effective approval.
