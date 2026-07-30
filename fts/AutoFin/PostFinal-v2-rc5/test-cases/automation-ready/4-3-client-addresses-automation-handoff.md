# Automation handoff: 4.3-client-addresses

## Статус

- Scope: `4-3-client-addresses`
- Основной файл для автоматизации: `fts/AutoFin/PostFinal-v2-rc5/test-cases/automation-ready/4-3-client-addresses.md`
- Baseline FT-first файл не переписывался: `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-client-addresses.md`
- Всего TC: `59`
- `confirmed`: `56`
- `implementation-defect`: `3`
- `blocked-observability`: `0`
- `needs-test-data`: `0`

## UI evidence

Evidence перенесён из ветки `codex/postfinal-v2-rc5-client-addresses-ui-calibration`, commit `d407d14662c9c64e30e83ea11926a78be6a4b58c`.

Локальный каталог evidence:

`fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/`

Ключевые файлы:

- `ui-validation-report.md`
- `ui-evidence-index.md`
- `evidence/per-tc/`
- `evidence/screenshots/`

## Подтвержденные решения после UI calibration

### TC-ADDR-053

Классификация: `confirmed`.

Решение: если ФТ ограничивает почтовый индекс 6 цифрами, поведение UI `4430179` → `443017` считается корректным enforcement: 7-я цифра игнорируется/обрезается, итоговое значение валидно.

### TC-ADDR-061

Классификация: `confirmed`.

Решение: по исходному ФТ поле `Улица` фактического адреса было обязательным, но пользователь сообщил уточнение БА из багтрекера: “поле улица делаем необязательным для фактического адреса тоже”. Поэтому TC переписан на проверку необязательности поля.

## Known implementation defects

Эти TC остаются FT-based и должны автоматизироваться как known failing до исправления реализации:

| TC-ID | Поле | Ожидание по ФТ | Текущее UI-поведение |
|---|---|---|---|
| `TC-ADDR-021` | `Корпус` адреса регистрации | numeric-only | UI принимает часть нечисловых значений |
| `TC-ADDR-023` | `Квартира` адреса регистрации | numeric-only | UI принимает часть нечисловых значений |
| `TC-ADDR-049` | `Квартира` фактического адреса | numeric-only | UI принимает часть нечисловых значений |

## Правило для автоматизатора

- `confirmed`: автоматизировать как обычный passing test.
- `implementation-defect`: автоматизировать как known failing / expected failure до исправления дефекта.
- Не переписывать expected result под текущее UI-поведение, если оно противоречит ФТ или принятому уточнению БА.
