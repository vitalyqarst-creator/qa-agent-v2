# Формат независимого результата review practical v0.9

```json
{
  "review_manifest_sha256": "<sha256 manifest>",
  "scope_id": "<scope id from manifest>",
  "scope_slug": "<scope slug from manifest>",
  "review_mode": "matrix",
  "execution_surface": "codex-thread",
  "reviewer_thread_id": "<другая верхнеуровневая Codex-сессия>",
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

Для scope, у которого manifest содержит `reviewer_receipt_contract`, reviewer
использует компактный вариант вместо массива `independent_obligations`:

```json
{
  "independent_obligation_set": {
    "source_anchor": "Самостоятельно прочитаны исходные материалы и scope-obligations.json из immutable snapshot.",
    "statement": "Самостоятельно восстановлен и проверен полный набор активных обязательств с их контекстами, границами, условиями и исключениями.",
    "scope_obligations_sha256": "<из reviewer_receipt_contract manifest>",
    "active_obligation_count": 50,
    "active_obligation_ids_sha256": "<из reviewer_receipt_contract manifest>"
  }
}
```

`source_anchor` и `statement` reviewer формулирует самостоятельно после
чтения snapshot. Значения SHA-256 и количество обязательств должны совпасть
с `reviewer_receipt_contract`, но controller не передаёт reviewer-у готовый
список `OBL-*` и не подменяет его вывод. Компактный вариант сохраняет полное
покрытие по digest immutable snapshot и не раздувает ответ повторением
исходных формулировок.

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
шаге: при неизвестной навигации открытый экран указывается в предусловии и
связан с `SETUP-NAV-*`. Для каждого DaData-сценария потребуй сохранённый
`FX-DADATA-*` с используемыми literals либо точные свойства отсутствующего
ответа и явный способ его подготовки. «Известная организация» или
«подготовить организацию» без этих данных — blocking finding.
Не допускай предпосылку «получен список DaData», когда сам TC вводит запрос
или выбирает подсказку: это дублирует trigger-state. Проверяй русский язык
runtime-полей и отклоняй английские служебные формулировки наподобие
`frozen profile`.

При восстановлении нельзя упрощать исходную норму до более широкого утверждения:
обязательно сохраняй контекст выполнения (например, создание и
редактирование), кванторы, граничные значения, условия и исключения. Если
разные контексты или классы входных данных дают самостоятельные проверяемые
потоки, они должны быть разложены на разные `OBL-*`/matrix rows/TC.

Reviewer сам проверяет `scenario_consolidation`, а не доверяет prose writer-а:
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

Raw submission ограничен размером, указанным в `reviewer_receipt_contract`
manifest (по умолчанию не более 24 KiB). Если первый ответ не проходит этот
контракт, controller не просит reviewer-а «сжать» уже вынесенный verdict и не
переписывает receipt: он фиксирует невалидный dispatch и при необходимости
запускает новый независимый review по тому же immutable snapshot.

После `changes-required` controller сам выполняет triage raw findings, затем
немедленно финализирует этот же неизменённый raw verdict до любой writer-
доработки. Reviewer не определяет расход revision budget, не меняет
`workflow-state.json` и не помечает свой verdict как effective approval.
