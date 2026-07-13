# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`.
- Активный source set: `source/FT4AutoFinFinal.docx`, `.xhtml`, `.pdf`.
- Родительский подтверждённый scope: `visual-assessment-criteria` внутри карточки заявки.
- Текущий canary — внутренний conditional-state пакет, не новый внешний scope.

## Scope Identity

- `scope_slug`: `visual-assessment-conditional-state-shadow`.
- Разделы: `4.3` / Table 4 и Appendix 1 только как dependency dictionary.
- Цель: проверить standard structured pipeline на наблюдаемых переходах состояния поля визуальной оценки.

## Что Входит В Scope

- Начальное значение `Визуальная информация = Нет`, `SRC-002.P02`, `BSR 312`.
- Показ списка при `Визуальная информация = Да`, `SRC-003.P01`, `BSR 314`.
- Скрытие списка при `Визуальная информация = Нет`, `SRC-003.P02`, `BSR 314`.
- Показ комментария при выборе `Другое` в категории `Признаки алкоголика`, `SRC-003.P06`, `BSR 317`, `DICT-101`.
- Одновременный выбор двух обычных значений, `SRC-003.P08`, `BSR 313`, `BSR 315`, `DICT-101`.

## Что Не Входит В Scope

- Полнота всех восьми категорий и всех значений `DICT-001`.
- Standalone-поля `Комментарий` из Appendix 1.
- Неподтверждённый механизм requiredness для пустого списка и пустого комментария `Другое`.
- Persistence, scoring, status changes, production promotion и изменение baseline.

## Разрешённые Источники

- Только Final source set, package notes и перечисленные current-source design artifacts.
- `AutoFinPreFinal.*`, production TC и предыдущие generated drafts запрещены как requirement evidence.

## Условие Старта

- Immutable package v5: 5 testable obligations и 1 non-blocking gap-obligation.
- Validate-only выбирает `conditional-state` и подтверждает production boundary.
- Один live exec cycle, без SDK fallback.
