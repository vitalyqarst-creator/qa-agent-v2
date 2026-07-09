# Coverage Gaps And BA Questions

## Coverage Gaps

| gap_id | source_ref | related_req | gap_type | description | downstream handling |
| --- | --- | --- | --- | --- | --- |
| `GAP-AW-001` | Related section 4.3 DaData rule, `BSR 325` | `BSR 119`; `BSR 144`; `BSR 325` | internal-observability | `BSR 325` says DaData-filled client address should fill model field `kladr`, but the selected UI scope has no observable artifact for model verification. | Not included in production UI TC; require API/DB/log evidence or UI evidence before executable coverage. |
| `GAP-AW-002` | Table 7 rows 35 | `BSR 124` | missing-ui-oracle | Registration postal index restriction says only 6 numeric chars, but source does not define exact UI reaction for non-numeric, shorter, or longer input. | Positive valid-value TC only; invalid classes require UI calibration or explicit validation oracle. |
| `GAP-AW-003` | Table 7 row 57 | `BSR 161` | missing-ui-oracle | Residence postal index restriction says only 6 numeric chars, but source does not define exact UI reaction for invalid values. | Positive valid-value TC only; invalid classes require UI calibration or explicit validation oracle. |
| `GAP-AW-004` | Table 7 rows 59, 62, 70 | `BSR 163`; `BSR 169`; `BSR 182` | missing-ui-oracle | Phone fields are restricted to 10 numeric chars and have a mask, but source does not define behavior for letters, fewer digits, more digits, paste, or save/transition rejection. | Positive mask/value TCs only; negative invalid classes deferred to UI calibration. |
| `GAP-AW-005` | Table 7 row 60 | `BSR 166` | missing-ui-oracle | E-mail rule requires `@` and one address, but source does not define exact reaction for missing `@`, multiple addresses, spaces, or invalid domain syntax. | Positive single-address TC only; invalid classes require explicit oracle. |
| `GAP-AW-006` | Table 7 rows 61-64 | `BSR 167`; `BSR 168` | setup-observability | Source says home/work phone visibility default is `Нет`, but exact initial block state and add-button labeling require UI evidence for a separate default-hidden TC. | Production TCs cover add and delete actions; default hidden state remains review risk. |
| `GAP-AW-007` | Table 7 rows 66-68 | `BSR 174`; `BSR 176`; `BSR 178` | missing-ui-oracle | Contact-person name fields allow text and hyphen, but source does not define behavior for digits, punctuation other than hyphen, spaces, mixed language, or paste. | Positive text/hyphen TCs only; invalid classes require UI calibration. |
| `GAP-AW-008` | Table 7 row 69 | `BSR 179` | closed-set-unclear | The source lists relation values but does not explicitly state the list is closed and contains no extra values. | Production TC checks listed values only; absence of extra values is not asserted. |
| `GAP-AW-009` | Table 7 row 71 | `BSR 185` | missing-ui-oracle | Birth date cannot be greater than current date, but source does not define exact reaction for future date. | Production TC covers visibility/valid past date; future-date negative requires UI calibration or exact validation oracle. |

## BA Questions

| question_id | related_gap | question |
| --- | --- | --- |
| `BA-AW-001` | `GAP-AW-002`; `GAP-AW-003`; `GAP-AW-004`; `GAP-AW-005`; `GAP-AW-007`; `GAP-AW-009` | Какая наблюдаемая UI-реакция должна использоваться для invalid input: фильтрация ввода, очистка, подсветка, сообщение, запрет сохранения или запрет перехода? |
| `BA-AW-002` | `GAP-AW-001` | Какой artifact разрешено использовать для проверки заполнения `kladr`: API response, DB check, audit log, browser devtools/mock, UI technical field? |
| `BA-AW-003` | `GAP-AW-006` | Как в UI называются виджеты добавления/удаления домашнего и рабочего телефона, и должен ли default-hidden state проверяться отдельным кейсом? |
| `BA-AW-004` | `GAP-AW-008` | Является ли список «Отношение к заявителю» закрытым справочником, где лишние значения должны отсутствовать? |

