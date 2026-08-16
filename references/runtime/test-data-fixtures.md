# Подготовка тестовых данных

## Назначение

Этот этап выполняется до matrix. Его результат — конкретные значения, с которыми можно выполнить будущий TC. Он не подменяет требования и не создаёт бизнес-правила.

## Приоритет источников

1. Уже сохранённая локальная fixture текущего FT-пакета.
2. Фактический provider интеграции, явно названный в ФТ: например DaData для DaData.
3. Проектный справочник или официальный публичный источник для статических значений.
4. Синтетический генератор для автономных данных формата: ФИО, телефон, e-mail, свободный текст, даты, уникальные имена. `api.randomdatatools.ru` допустим только в этом пункте.

Web search разрешён только для поиска авторитетного публичного статического источника. Он не заменяет ответ интеграции, стендовую сущность, роль или банковскую проверку.

## External provider fixture

Для интеграции агент обязан создать или найти `work/test-data/<scope>/fixture-catalog.json`.

Каждая запись содержит:

```json
{
  "fixture_id": "FX-PARTNER-DADATA-001",
  "purpose": "Подсказка организации и автозаполнение карточки партнёра",
  "source_type": "provider",
  "provider": "DaData",
  "request": {"query": "...", "endpoint": "..."},
  "runtime_data": {"suggestion": "...", "inn": "..."},
  "snapshot_path": "fixtures/FX-PARTNER-DADATA-001.response.json",
  "snapshot_sha256": "<64 hex>",
  "verified_at": "YYYY-MM-DDTHH:MM:SSZ"
}
```

Секреты и токены в catalog/snapshot не записываются. Для DaData сначала захвати воспроизводимую подсказку штатной командой `scripts/capture_dadata_fixture.py`; она использует только `DADATA_API_KEY` из окружения и сохраняет token-free snapshot.

```text
python scripts/capture_dadata_fixture.py --kind party --query <запрос> --fixture-id <FX-ID> --purpose <цель> --fixture-root <work/test-data/<scope>/fixtures>
python scripts/validate_fixture_catalog.py <work/test-data/<scope>/fixtures/fixture-catalog.json>
```

Команда выполняет два одинаковых запроса, отказывается сохранять нестабильную выбранную подсказку и добавляет в catalog конкретные поля ответа, которые writer обязан использовать как литералы в TC.

## Когда fixture не получена

Если источник недоступен, нет credentials, ответ нестабилен или не определён наблюдаемый UI-оракул:

- зафиксируй конкретную причину в `coverage-gaps.md`;
- сформулируй вопрос к БА/владельцу данных;
- не включай обязанность в executable matrix и canonical TC.

Фразы «нужна fixture», «подготовить значение», «запрос будет определён» не являются тестовыми данными.

## Проекция в тест-кейс

В production TC переносятся только tester-facing literals: точный запрос, организация/значение, необходимые реквизиты, исходное состояние. `fixture_id`, snapshot path, SHA-256, provider diagnostics и статусы остаются в work-каталоге.
