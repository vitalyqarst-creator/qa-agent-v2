# Coverage Gaps And BA Questions

## Coverage Gaps

| gap_id | source_ref | related_req | gap_type | description | downstream handling |
| --- | --- | --- | --- | --- | --- |
| `GAP-AW2-001` | Table 7 row 33; related section 4.3 DaData model rule | `BSR 119`; `BSR 325` | internal-observability | Source describes address decomposition and internal `kladr` model filling, but selected manual UI scope has no observable artifact for verifying model storage. | Keep out of UI TC until API, DB, log or observed UI evidence is allowed. |
| `GAP-AW2-002` | Table 7 rows 61-64 | `BSR 167`; `BSR 168`; `BSR 171`; `BSR 172` | setup-observability | Source defines home/work phone visibility defaults and add/delete actions, but exact widget labels and default-hidden evidence require UI observation. | Production TCs cover add/delete behavior; default-hidden micro-check remains a UI calibration question. |
| `GAP-AW2-003` | Table 7 row 69 | `BSR 179` | closed-set-unclear | Source lists relation values but does not explicitly state that no other relation values may appear. | TC checks listed values and `Иное`; absence of extra values is not asserted until BA confirms closed set. |
| `GAP-AW2-004` | Table 7 rows 35, 57, 59, 60, 62, 66-68, 70, 71 | `BSR 124`; `BSR 161`; `BSR 163`; `BSR 166`; `BSR 169`; `BSR 174`; `BSR 176`; `BSR 178`; `BSR 182`; `BSR 185` | ui-calibration-mechanism | Source-backed visible input restrictions define invalid classes, but do not define the exact UI rejection mechanism. | Candidate child obligations `SO-NEG-AW2-001`..`SO-NEG-AW2-011` are covered by candidate-negative TC; this parent gap keeps only the missing UI mechanism question. |

## BA Questions

| question_id | related_gap | question |
| --- | --- | --- |
| `BA-AW2-001` | `GAP-AW2-001` | Какой artifact разрешено использовать для проверки заполнения `kladr`: API response, DB check, audit log, browser devtools/mock, UI technical field? |
| `BA-AW2-002` | `GAP-AW2-002` | Как в UI называются виджеты добавления/удаления домашнего и рабочего телефона, и нужно ли default-hidden state проверять отдельным кейсом? |
| `BA-AW2-003` | `GAP-AW2-003` | Является ли список "Отношение к заявителю" закрытым справочником, где лишние значения должны отсутствовать? |
| `BA-AW2-004` | `GAP-AW2-004` | Какой наблюдаемый UI-механизм считать ожидаемым для invalid input: фильтрация ввода, очистка, подсветка, сообщение, запрет сохранения, запрет перехода или другое поведение? |
