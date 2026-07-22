# Production Global Rules

Этот файл — самодостаточная production-проекция глобальных правил полного
репозитория. Production bundle загружает её через
`production-instruction-loading.md`; корневой `AGENTS.md` полного development-
репозитория в bundle не входит.

## Источники и границы

- DOCX — source of truth, matching XHTML обязателен для machine-readable
  extraction. Без XHTML scope блокируется как `blocked-input`.
- PDF используется только для structural/visual cross-check; support и mockups
  не создают бизнес-правила.
- После выбора FT-пакета обязательный package-local `AGENT-NOTES.md`, если он
  существует.
- Не выдумывай поведение, поля, значения и интеграции. Неоднозначность оформляй
  как coverage gap с точным source locator.
- Справочник или фиксированный перечень извлекай полностью; конкретные
  тестовые данные должны быть source-backed и воспроизводимыми.

## Качество результата

- Один тест-кейс проверяет одну обязанность и имеет один основной ожидаемый
  результат; независимые atomic statements не склеиваются.
- Сохраняй точные requirement codes и полную трассировку к source assertions и
  obligations.
- Результат должен быть пригоден для ручного выполнения. Не выдавай UI-
  calibration candidate за исполнимый production-кейс.
- Старые test cases, benchmark/history и произвольные незарегистрированные файлы
  не являются model input.

## Исполнение

- Перед shell-командами используй сохранённый environment probe либо
  `scripts/probe_environment.py`; соблюдай UTF-8 policy и не предполагай shell.
- Этот downstream bundle не выполняет discovery и source qualification. До
  запуска ему передают независимо принятый manifest v4, compiler-v3 obligations,
  hash-bound semantic projection и зарегистрированную границу scope.
- Загружай только scenario `iteration.deterministic_production` из
  `production-instruction-loading.md`.
- `ft-agent run` работает только с закрытым schema-v2 config и новым immutable
  output directory. Canonical, source files и workflow state не изменяются.
- Допустимые успешные terminal statuses: `accepted-shadow` для полностью
  исполнимого набора и `accepted-with-calibration-pending`, если reviewer честно
  подтвердил calibration-кандидаты как `calibration-pending`. Второй статус
  всегда `promotion_eligible=false`; publication не входит в production run.
