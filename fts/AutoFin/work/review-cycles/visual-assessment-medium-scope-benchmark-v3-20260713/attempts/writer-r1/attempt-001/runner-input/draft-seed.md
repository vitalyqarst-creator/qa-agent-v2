# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

## TC-VAMB-001

**Название:** [SEED:title:ATOM-001]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-001; ATOM-001; SRC-002.P01; BSR 311; SRC-001; SRC-002

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Визуальная информация` отображается всегда.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-002

**Название:** [SEED:title:ATOM-002]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-002; ATOM-002; SRC-002.P02; BSR 312; SRC-002

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение по умолчанию равно `Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-003

**Название:** [SEED:title:ATOM-003+ATOM-004]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-003; ATOM-003; SRC-002.P03; BSR 313; SRC-002; BSR 314; OBL-004; ATOM-004; SRC-003.P01; SRC-003

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После выбора `Да` отображается список `Параметры визуальной оценки`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-004

**Название:** [SEED:title:ATOM-005]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-005; ATOM-005; SRC-003.P02; BSR 314; SRC-003

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Когда `Визуальная информация` не равна `Да`, список параметров не отображается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-005

**Название:** [SEED:title:ATOM-006]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-006; ATOM-006; SRC-003.P03; BSR 315; SRC-003-SRC-052; DICT-001

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Список содержит восемь групп и полный состав значений из `DICT-001`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-006

**Название:** [SEED:title:ATOM-007]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-007; ATOM-007; SRC-003.P04; BSR 315; SRC-005-SRC-050; DICT-001

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Каждое обычное значение `DICT-001` доступно как checkbox.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-007

**Название:** [SEED:title:ATOM-008]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-008; ATOM-008; SRC-003.P05; BSR 316; SRC-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `ui-calibration-required`; `candidate-ui-calibration`: при `Визуальная информация = Да` и пустом выборе выполнить следующее доступное действие формы и зафиксировать фактическое видимое состояние блока и результат действия, не утверждая текст сообщения, подсветку или blocked transition.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-008

**Название:** [SEED:title:ATOM-009]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-009; ATOM-009; SRC-003.P06; BSR 317; SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; DICT-001; DICT-108

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Выбор checkbox `Другое` отображает текстовое поле комментария.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-009

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-010; ATOM-010; SRC-003.P07; BSR 317; SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; DICT-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `ui-calibration-required`; `candidate-ui-calibration`: выбрать `Другое`, оставить открывшийся комментарий пустым, выполнить следующее доступное действие формы и зафиксировать фактическое видимое состояние поля и результат действия, не утверждая текст сообщения, подсветку или blocked transition.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-010

**Название:** [SEED:title:ATOM-011]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-011; ATOM-011; SRC-010.P01; SRC-010; SRC-020; SRC-051; SRC-052

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Standalone-строки `Комментарий` отображаются как отдельные поля ввода и не смешиваются с `Другое`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-011

**Название:** [SEED:title:ATOM-012]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-012; ATOM-012; SRC-010.P02; SRC-010; SRC-020; SRC-051; SRC-052

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После ввода текста `Наблюдение теста` standalone-поле отображает значение `Наблюдение теста`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-VAMB-012

**Название:** [SEED:title:ATOM-013]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-013; ATOM-013; SRC-003.P08; BSR 313; BSR 315; SRC-002; SRC-003; SRC-005-SRC-050; DICT-001

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После выбора двух обычных значений оба checkbox остаются выбранными одновременно.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
