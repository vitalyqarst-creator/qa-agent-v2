# Automation-ready: 4-3-current-passport-data

> Источник baseline: `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-current-passport-data.md`.
> UI evidence: `origin/codex/postfinal-v2-rc5-three-files-ui-pass`, commit `2ed11a295467d6beba1809f8395a340c3921b87c`.
> Automation-ready версия не заменяет FT-first baseline и отражает executable UI flow по результатам UI pass 2026-07-30 и последующих owner clarifications.

## Общие предусловия для автоматизации

1. Открыть тестовый стенд AutoFin.
2. После входа выбрать строку `cff` на launch screen и нажать `ЗАПУСТИТЬ`.
3. В списке заявок нажать `СОЗДАТЬ ЗАЯВКУ`.
4. Убедиться, что открыта карточка `Заявка`.

## Общие automation notes

- Базовое предусловие каждого кейса: открыта карточка `Заявка`; автоматизатор сам выбирает стратегию создания/очистки заявки.
- Baseline test-cases в `test-cases/` не изменяются.
- Если в кейсе указана DaData-подсказка, automation вводит значение медленно, ждёт `li.ui-menu-item`, выбирает exact option и только затем делает blur/assert.
- Для masked inputs использовать keyboard/type, затем blur. Не использовать raw value injection, если нужно проверить работу маски.
- UI evidence paths указывают на артефакты из evidence branch; в этой ветке automation-ready файлы ссылаются на них как на опубликованный источник UI pass.

# FT-first baseline: 4-3-current-passport-data

> Финальный статус: `reviewed-with-known-findings`.
> Набор создан из shadow draft attempt `20260727-4-3-current-passport-data-source-first-attempt-021` после passed production suite gate, но reviewer verdict = `changes-required`.
> Это не `signed-off` и не production-ready sign-off. Известный дефект покрытия: `SRC-PASS-CUR-010` / `OBL-PASS-CUR-027` не материализован как отдельная obligation/case.
> Подробности: `fts/AutoFin/PostFinal-v2-rc5/work/iterations/20260727-4-3-current-passport-data-source-first-attempt-021/finalization-receipt.json`.

# Тест-кейсы: Карточка «Заявка» / Блок «Паспортные данные»

## TC-PASSCUR-001

**№:** 1
**Название:** Поле ручного ввода «Кем выдан» обязательно, если «Ввести вручную подразделение» = «Да»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-033; ATOM-033; ASSERT-PASS-CUR-033

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Кем выдан: оставить пустым.

### Шаги

1. Установить переключатель «Ввести вручную подразделение» в значение «Да».
2. Оставить поле «Кем выдан» пустым.
3. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Выберите значение».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-002

**№:** 2
**Название:** Поле «Кем выдан» в режиме DaData обязательно, если «Ввести вручную подразделение» = «Нет»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-032; ATOM-032; ASSERT-PASS-CUR-032

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Кем выдан: оставить пустым.

### Шаги

1. Установить переключатель «Ввести вручную подразделение» в значение «Нет».
2. Оставить поле «Кем выдан» пустым.
3. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Выберите значение».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-003

**№:** 3
**Название:** Поле «Кем выдан» предзаполняется по коду подразделения
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-015; ATOM-015; ASSERT-PASS-CUR-015; BSR 94

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Fixture DaData: `FX-DADATA-FMS-POS-001`.
- Запрос: `772-053`.
- Точное предложение: `ОВД ЗЮЗИНО Г. МОСКВЫ`.

### Шаги

1. Установить переключатель `Ввести вручную подразделение` в значение `Нет`.
2. Ввести `772-053` в поле `Код подразделения`.
3. Убрать фокус с поля `Код подразделения`.
4. Поставить фокус в поле `Кем выдан`.
5. Дождаться появления dropdown `li.ui-menu-item`.
6. Выбрать exact option `ОВД ЗЮЗИНО Г. МОСКВЫ`.
7. Убрать фокус с поля `Кем выдан`.
8. Проверить значение и состояние поля `Кем выдан`.

### Итоговый ожидаемый результат

Поле `Кем выдан` отображает значение `ОВД ЗЮЗИНО Г. МОСКВЫ`; поле не находится в состоянии invalid. Порядок и количество вариантов dropdown не проверяются.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для `Кем выдан` использовать `FX-DADATA-FMS-POS-001`: ввести `772-053`, blur `Код подразделения`, focus `Кем выдан`, дождаться `li.ui-menu-item`, выбрать `ОВД ЗЮЗИНО Г. МОСКВЫ`, затем blur.

## TC-PASSCUR-004

**№:** 4
**Название:** Отображение поля ручного ввода «Кем выдан» при включенном ручном вводе
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-019; ATOM-019; ASSERT-PASS-CUR-019; BSR 98

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Установить переключатель «Ввести вручную подразделение» в значение «Да».
2. Проверить отображение поля «Кем выдан».

### Итоговый ожидаемый результат

Отображается текстовое поле «Кем выдан» для ручного ввода.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-005

**№:** 5
**Название:** Отображение списка «Кем выдан» при выключенном ручном вводе
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-014; ATOM-014; ASSERT-PASS-CUR-014; BSR 93

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Установить переключатель `Ввести вручную подразделение` в значение `Нет`.
2. Ввести `772-053` в поле `Код подразделения`.
3. Убрать фокус с поля `Код подразделения`.
4. Поставить фокус в поле `Кем выдан`.
5. Дождаться появления dropdown `li.ui-menu-item`.
6. Проверить, что поле `Кем выдан` работает как раскрывающийся список подсказок.

### Итоговый ожидаемый результат

Отображается раскрывающийся список «Кем выдан».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для `Кем выдан` использовать `FX-DADATA-FMS-POS-001`: ввести `772-053`, blur `Код подразделения`, focus `Кем выдан`, дождаться `li.ui-menu-item`, выбрать `ОВД ЗЮЗИНО Г. МОСКВЫ`, затем blur.

## TC-PASSCUR-006

**№:** 6
**Название:** Значение по умолчанию переключателя «Клиент менял паспорт»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-028; ATOM-028; ASSERT-PASS-CUR-028; BSR 104

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Ожидаемое значение: `Нет`.

### Шаги

1. Не взаимодействуя с переключателем «Клиент менял паспорт», проверить его первоначальное значение `Нет`.

### Итоговый ожидаемый результат

Переключатель «Клиент менял паспорт» имеет значение «Нет».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-007

**№:** 7
**Название:** Отображение переключателя «Клиент менял паспорт» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-027; ATOM-027; ASSERT-PASS-CUR-027; BSR 103

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение переключателя «Клиент менял паспорт».

### Итоговый ожидаемый результат

Переключатель «Клиент менял паспорт» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-008

**№:** 8
**Название:** Поле «Место рождения» обязательно для заполнения
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-035; ATOM-035; ASSERT-PASS-CUR-035

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Место рождения: оставить пустым.

### Шаги

1. Оставить поле «Место рождения» пустым.
2. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Обязательно к заполнению».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-009

**№:** 9
**Название:** Отображение поля «Место рождения» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-026; ATOM-026; ASSERT-PASS-CUR-026; BSR 102

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля «Место рождения».

### Итоговый ожидаемый результат

Поле «Место рождения» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-010

**№:** 10
**Название:** Нечисловые символы в поле «Номер»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-008; ATOM-008; ASSERT-PASS-CUR-008; BSR 88

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `123A56`.
- Недопустимое значение: `123 56`.
- Недопустимое значение: `123@56`.
- Недопустимое значение: `123.56`.
- Недопустимое значение: `123-56`.

### Шаги

1. Ввести `123A56` в поле «Номер» и проверить, что нечисловой символ не вводится.
2. Очистить поле «Номер».
3. Ввести `123 56` в поле «Номер» и проверить, что пробел не вводится.
4. Очистить поле «Номер».
5. Ввести `123@56` в поле «Номер» и проверить, что символ `@` не вводится.
6. Очистить поле «Номер».
7. Ввести `123.56` в поле «Номер» и проверить, что точка не вводится.
8. Очистить поле «Номер».
9. Ввести `123-56` в поле «Номер» и проверить, что дефис не вводится.
10. Очистить поле «Номер».

### Итоговый ожидаемый результат

Нечисловой символ фильтруется маской. Если после фильтрации значение остаётся неполным, после blur поле `Номер` очищается и отображается сообщение `Обязательно к заполнению`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Вводить через keyboard/type и обязательно выполнять blur; для short/mixed masked values проверять clear-on-blur и message/state, а не абстрактную невалидность.

## TC-PASSCUR-011

**№:** 11
**Название:** Ввод более шести цифр в поле «Номер»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-007; ATOM-007; ASSERT-PASS-CUR-007; BSR 88

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `1234567`.

### Шаги

1. Ввести `1234567` в поле «Номер».
2. Проверить отображаемое значение поля «Номер».
3. Очистить поле «Номер».

### Итоговый ожидаемый результат

Седьмой символ не вводится; в поле остается значение `123456` длиной 6 символов.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Overflow проверяется как truncation/ignore by mask: лишний символ не становится отдельной invalid value.

## TC-PASSCUR-012

**№:** 12
**Название:** Короткое значение в поле «Номер»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-007; ATOM-007; ASSERT-PASS-CUR-007; BSR 88; SO-CAL-B9AA3D5996B08EBD
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `12345`.

### Шаги

1. Ввести тестовое значение в поле `Номер` через keyboard/type.
2. Убрать фокус с поля `Номер`.
3. Проверить отображаемое значение и сообщение под полем.
4. Очистить поле `Номер` при необходимости.

### Итоговый ожидаемый результат

После blur короткое значение очищается; поле `Номер` находится в invalid/required state и отображает сообщение `Обязательно к заполнению`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Вводить через keyboard/type и обязательно выполнять blur; для short/mixed masked values проверять clear-on-blur и message/state, а не абстрактную невалидность.

## TC-PASSCUR-013

**№:** 13
**Название:** Шестизначный номер паспорта
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-007; ATOM-007; ASSERT-PASS-CUR-007; BSR 88

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое значение: `123456`.

### Шаги

1. Ввести `123456` в поле «Номер».
2. Проверить отображаемое значение поля «Номер».
3. Очистить поле «Номер».

### Итоговый ожидаемый результат

Поле «Номер» отображает значение `123456`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-014

**№:** 14
**Название:** Шесть одинаковых цифр подряд в поле «Номер»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-009; ATOM-009; ASSERT-PASS-CUR-009; BSR 89

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `111111`.

### Шаги

1. Ввести `111111` в поле «Номер».
2. Проверить состояние поля и сообщение под ним.

### Итоговый ожидаемый результат

Значение `111111` вводится, поле подсвечивается красным, под полем отображается сообщение «Не должно быть шести одинаковых цифр подряд».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-015

**№:** 15
**Название:** Поле «Номер» обязательно для заполнения
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-030; ATOM-030; ASSERT-PASS-CUR-030

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Номер: оставить пустым.

### Шаги

1. Оставить поле «Номер» пустым.
2. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Обязательно к заполнению».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-016

**№:** 16
**Название:** Отображение поля «Номер» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-006; ATOM-006; ASSERT-PASS-CUR-006; BSR 87

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля «Номер».

### Итоговый ожидаемый результат

Поле «Номер» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-017

**№:** 17
**Название:** Значение по умолчанию переключателя «Ввести вручную подразделение»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-018; ATOM-018; ASSERT-PASS-CUR-018; BSR 97

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Ожидаемое значение: `Нет`.

### Шаги

1. Не взаимодействуя с переключателем «Ввести вручную подразделение», проверить его первоначальное значение `Нет`.

### Итоговый ожидаемый результат

Переключатель «Ввести вручную подразделение» имеет значение «Нет».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-018

**№:** 18
**Название:** Выбор значения «Кем выдан» из предложений DaData
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-016; ATOM-016; ASSERT-PASS-CUR-016; BSR 95

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Fixture DaData: `FX-DADATA-FMS-POS-001`.
- Запрос: `772-053`.
- Точное предложение: `ОВД ЗЮЗИНО Г. МОСКВЫ`.

### Шаги

1. Установить переключатель `Ввести вручную подразделение` в значение `Нет`.
2. Ввести `772-053` в поле `Код подразделения`.
3. Убрать фокус с поля `Код подразделения`.
4. Поставить фокус в поле `Кем выдан`.
5. Дождаться появления dropdown `li.ui-menu-item`.
6. Выбрать exact option `ОВД ЗЮЗИНО Г. МОСКВЫ`.
7. Убрать фокус с поля `Кем выдан`.
8. Проверить значение и состояние поля `Кем выдан`.

### Итоговый ожидаемый результат

Поле `Кем выдан` отображает значение `ОВД ЗЮЗИНО Г. МОСКВЫ`; поле не находится в состоянии invalid. Порядок и количество вариантов dropdown не проверяются.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для `Кем выдан` использовать `FX-DADATA-FMS-POS-001`: ввести `772-053`, blur `Код подразделения`, focus `Кем выдан`, дождаться `li.ui-menu-item`, выбрать `ОВД ЗЮЗИНО Г. МОСКВЫ`, затем blur.

## TC-PASSCUR-019

**№:** 19
**Название:** Отображение переключателя «Ввести вручную подразделение» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-017; ATOM-017; ASSERT-PASS-CUR-017; BSR 96

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение переключателя «Ввести вручную подразделение».

### Итоговый ожидаемый результат

Переключатель «Ввести вручную подразделение» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-020

**№:** 20
**Название:** Просрочка паспорта на 91-й день после 45-летия
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-023; ATOM-023; ASSERT-PASS-CUR-023; BSR 100

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое граничное условие: `дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 91 день`.

### Шаги

1. Подготовить условие `дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 91 день`.
2. Ввести рассчитанную дату выдачи в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Сохранение блокируется; отображается подсказка «Паспорт недействителен (просрочен)».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-021

**№:** 21
**Название:** Дата выдачи за день до 14-летия клиента
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-021; ATOM-021; ASSERT-PASS-CUR-021; BSR 100

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое граничное условие: `дата 14-летия - 1 день`.

### Шаги

1. Рассчитать дату по условию `дата 14-летия - 1 день`.
2. Ввести рассчитанную дату в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Сохранение блокируется с подсказкой «Выдача паспорта предусмотрена с 14 лет».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-022

**№:** 22
**Название:** Просрочка паспорта на 91-й день после 20-летия
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-022; ATOM-022; ASSERT-PASS-CUR-022; BSR 100

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое граничное условие: `дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 91 день`.

### Шаги

1. Подготовить условие `дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 91 день`.
2. Ввести рассчитанную дату выдачи в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Сохранение блокируется; отображается подсказка «Паспорт недействителен (просрочен)».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-023

**№:** 23
**Название:** Срок действия паспорта на 90-й день после 45-летия
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-023; ATOM-023; ASSERT-PASS-CUR-023; BSR 100; SO-CAL-130A52DD73C6B7BF
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое граничное условие: `дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 90 дней`.

### Шаги

1. Подготовить условие `дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 90 дней`.
2. Ввести рассчитанную дату выдачи в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.
4. Проверить отображаемое значение и состояние поля `Дата выдачи`.

### Итоговый ожидаемый результат

Поле `Дата выдачи` отображает рассчитанную граничную дату и не находится в invalid state. Точный текст сообщения не проверяется.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-024

**№:** 24
**Название:** Дата выдачи в день 14-летия клиента
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-021; ATOM-021; ASSERT-PASS-CUR-021; BSR 100; SO-CAL-E157E14D70EE210D
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое граничное условие: `дата 14-летия`.

### Шаги

1. Рассчитать условие `дата 14-летия`.
2. Ввести рассчитанную дату в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.
4. Проверить отображаемое значение и состояние поля `Дата выдачи`.

### Итоговый ожидаемый результат

Поле `Дата выдачи` отображает рассчитанную дату и не находится в invalid state. Точный текст сообщения не проверяется.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-025

**№:** 25
**Название:** Срок действия паспорта на 90-й день после 20-летия
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-022; ATOM-022; ASSERT-PASS-CUR-022; BSR 100; SO-CAL-1E45C304CD480613
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое граничное условие: `дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 90 дней`.

### Шаги

1. Подготовить условие `дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 90 дней`.
2. Ввести рассчитанную дату выдачи в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.
4. Проверить отображаемое значение и состояние поля `Дата выдачи`.

### Итоговый ожидаемый результат

Поле `Дата выдачи` отображает рассчитанную граничную дату и не находится в invalid state. Точный текст сообщения не проверяется.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-026

**№:** 26
**Название:** Дата выдачи паспорта в день 45-летия
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-024; ATOM-024; ASSERT-PASS-CUR-024; BSR 100; SO-CAL-1E93A6C34ABC8C9C
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Тестовое граничное условие: `дата выдачи = дата 45-летия`.

### Шаги

1. Подготовить условие `дата выдачи = дата 45-летия`.
2. Ввести рассчитанную дату выдачи в поле «Дата выдачи».
3. Убрать фокус с поля `Дата выдачи`, затем нажать кнопку `ДАЛЕЕ`.
4. Проверить отображаемое значение и состояние поля `Дата выдачи`.

### Итоговый ожидаемый результат

Поле `Дата выдачи` отображает рассчитанную дату и не находится в invalid state. Точный текст сообщения не проверяется.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-027

**№:** 27
**Название:** Дата выдачи позже текущей даты
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-025; ATOM-025; ASSERT-PASS-CUR-025; BSR 101

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение больше текущей даты: `текущая дата + 1 день`.

### Шаги

1. Рассчитать дату `текущая дата + 1 день` относительно даты выполнения проверки.
2. Ввести рассчитанное значение `текущая дата + 1 день` в поле «Дата выдачи».
3. Проверить сообщение под полем.
4. Очистить поле «Дата выдачи».

### Итоговый ожидаемый результат

Под полем отображается текст «Дата не может быть больше <текущая дата в формате ДД.ММ.ГГГГ>».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-028

**№:** 28
**Название:** Допустимые граничные значения поля «Дата выдачи»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-025; ATOM-025; ASSERT-PASS-CUR-025; BSR 101

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое граничное значение: `текущая дата - 1 день`.
- Допустимое граничное значение: `текущая дата`.

### Шаги

1. Рассчитать значения `текущая дата - 1 день` и `текущая дата` относительно даты выполнения проверки.
2. Ввести `текущая дата - 1 день` в поле «Дата выдачи».
3. Проверить, что поле «Дата выдачи» отображает рассчитанное значение `текущая дата - 1 день`.
4. Очистить поле «Дата выдачи».
5. Ввести `текущая дата` в поле «Дата выдачи».
6. Проверить, что поле «Дата выдачи» отображает рассчитанное значение `текущая дата`.
7. Очистить поле «Дата выдачи».

### Итоговый ожидаемый результат

Поле «Дата выдачи» отображает рассчитанное значение после ввода каждой из дат: `текущая дата - 1 день` и `текущая дата`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-029

**№:** 29
**Название:** Поле «Дата выдачи» обязательно для заполнения
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-034; ATOM-034; ASSERT-PASS-CUR-034

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Дата выдачи: оставить пустым.

### Шаги

1. Оставить поле «Дата выдачи» пустым.
2. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Введите дату».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-030

**№:** 30
**Название:** Отображение поля «Дата выдачи» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-020; ATOM-020; ASSERT-PASS-CUR-020; BSR 99

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля «Дата выдачи».

### Итоговый ожидаемый результат

Поле «Дата выдачи» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-031

**№:** 31
**Название:** Нечисловые символы в поле «Серия»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-004; ATOM-004; ASSERT-PASS-CUR-004; BSR 85

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `12A4`.
- Недопустимое значение: `12 4`.
- Недопустимое значение: `12@4`.
- Недопустимое значение: `12.4`.
- Недопустимое значение: `12-4`.

### Шаги

1. Ввести `12A4` в поле «Серия» и проверить, что нечисловой символ не вводится.
2. Очистить поле «Серия».
3. Ввести `12 4` в поле «Серия» и проверить, что пробел не вводится.
4. Очистить поле «Серия».
5. Ввести `12@4` в поле «Серия» и проверить, что символ `@` не вводится.
6. Очистить поле «Серия».
7. Ввести `12.4` в поле «Серия» и проверить, что точка не вводится.
8. Очистить поле «Серия».
9. Ввести `12-4` в поле «Серия» и проверить, что дефис не вводится.
10. Очистить поле «Серия».

### Итоговый ожидаемый результат

Нечисловой символ фильтруется маской. Если после фильтрации значение остаётся неполным, после blur поле `Серия` очищается и отображается сообщение `Обязательно к заполнению`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Вводить через keyboard/type и обязательно выполнять blur; для short/mixed masked values проверять clear-on-blur и message/state, а не абстрактную невалидность.

## TC-PASSCUR-032

**№:** 32
**Название:** Ввод более четырех цифр в поле «Серия»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-003; ATOM-003; ASSERT-PASS-CUR-003; BSR 85

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `12345`.

### Шаги

1. Ввести `12345` в поле «Серия».
2. Проверить отображаемое значение поля «Серия».
3. Очистить поле «Серия».

### Итоговый ожидаемый результат

Пятый символ не вводится; в поле остается значение `1234` длиной 4 символа.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Overflow проверяется как truncation/ignore by mask: лишний символ не становится отдельной invalid value.

## TC-PASSCUR-033

**№:** 33
**Название:** Короткое значение в поле «Серия»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-003; ATOM-003; ASSERT-PASS-CUR-003; BSR 85; SO-CAL-B1B43294C3EFD8EC
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `123`.

### Шаги

1. Ввести тестовое значение в поле `Серия` через keyboard/type.
2. Убрать фокус с поля `Серия`.
3. Проверить отображаемое значение и сообщение под полем.
4. Очистить поле `Серия` при необходимости.

### Итоговый ожидаемый результат

После blur короткое значение очищается; поле `Серия` находится в invalid/required state и отображает сообщение `Обязательно к заполнению`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Вводить через keyboard/type и обязательно выполнять blur; для short/mixed masked values проверять clear-on-blur и message/state, а не абстрактную невалидность.

## TC-PASSCUR-034

**№:** 34
**Название:** Четырехзначная серия паспорта
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-003; ATOM-003; ASSERT-PASS-CUR-003; BSR 85

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое значение: `1234`.

### Шаги

1. Ввести `1234` в поле «Серия».
2. Проверить отображаемое значение поля «Серия».
3. Очистить поле «Серия».

### Итоговый ожидаемый результат

Поле «Серия» отображает значение `1234`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-035

**№:** 35
**Название:** Три одинаковые цифры подряд в поле «Серия»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-005; ATOM-005; ASSERT-PASS-CUR-005; BSR 86

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `111`.

### Шаги

1. Ввести `111` в поле «Серия».
2. Проверить состояние поля и сообщение под ним.

### Итоговый ожидаемый результат

Значение `111` вводится, поле подсвечивается красным, под полем отображается сообщение «Не должно быть трех одинаковых цифр подряд».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-036

**№:** 36
**Название:** Поле «Серия» обязательно для заполнения
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-029; ATOM-029; ASSERT-PASS-CUR-029

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Серия: оставить пустым.

### Шаги

1. Оставить поле «Серия» пустым.
2. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Обязательно к заполнению».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-037

**№:** 37
**Название:** Отображение поля «Серия» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-002; ATOM-002; ASSERT-PASS-CUR-002; BSR 84

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля «Серия».

### Итоговый ожидаемый результат

Поле «Серия» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-038

**№:** 38
**Название:** Нечисловые символы в поле «Код подразделения»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-012; ATOM-012; ASSERT-PASS-CUR-012; BSR 91

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `123A56`.
- Недопустимое значение: `123 56`.
- Недопустимое значение: `123@56`.
- Недопустимое значение: `123.56`.
- Недопустимое значение: `123-56`.

### Шаги

1. Ввести `123A56` в поле «Код подразделения» и проверить, что нечисловой символ не вводится.
2. Очистить поле «Код подразделения».
3. Ввести `123 56` в поле «Код подразделения» и проверить, что пробел не вводится.
4. Очистить поле «Код подразделения».
5. Ввести `123@56` в поле «Код подразделения» и проверить, что символ `@` не вводится.
6. Очистить поле «Код подразделения».
7. Ввести `123.56` в поле «Код подразделения» и проверить, что точка не вводится.
8. Очистить поле «Код подразделения».
9. Ввести `123-56` в поле «Код подразделения» и проверить, что дефис не вводится.
10. Очистить поле «Код подразделения».

### Итоговый ожидаемый результат

Нечисловой символ фильтруется маской. Если после фильтрации значение остаётся неполным, после blur поле `Код подразделения` очищается или остаётся invalid и отображает сообщение `Код подразделения не в формате 000-000`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Вводить через keyboard/type и обязательно выполнять blur; для short/mixed masked values проверять clear-on-blur и message/state, а не абстрактную невалидность.

## TC-PASSCUR-039

**№:** 39
**Название:** Форматирование кода подразделения
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-013; ATOM-013; ASSERT-PASS-CUR-013; BSR 92

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое значение: `123456`.

### Шаги

1. Ввести `123456` в поле «Код подразделения».
2. Проверить отображаемое значение поля «Код подразделения».

### Итоговый ожидаемый результат

Поле «Код подразделения» отображает значение `123-456`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-040

**№:** 40
**Название:** Ввод более шести цифр в поле «Код подразделения»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-011; ATOM-011; ASSERT-PASS-CUR-011; BSR 91

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `1234567`.

### Шаги

1. Ввести `1234567` в поле «Код подразделения».
2. Проверить отображаемое значение поля.
3. Очистить поле «Код подразделения».

### Итоговый ожидаемый результат

Седьмой числовой символ игнорируется маской; поле `Код подразделения` отображает значение `123-456`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Overflow проверяется как truncation/ignore by mask: лишний символ не становится отдельной invalid value.

## TC-PASSCUR-041

**№:** 41
**Название:** Короткое значение в поле «Код подразделения»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-011; ATOM-011; ASSERT-PASS-CUR-011; BSR 91; SO-CAL-7FE2E4D50CB184D5
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Недопустимое значение: `12345`.

### Шаги

1. Ввести `12345` в поле `Код подразделения` через keyboard/type.
2. Убрать фокус с поля `Код подразделения`.
3. Проверить отображаемое значение и сообщение под полем.
4. Очистить поле `Код подразделения` при необходимости.

### Итоговый ожидаемый результат

После blur короткое значение не принимается как valid; поле `Код подразделения` находится в invalid state и отображает сообщение `Код подразделения не в формате 000-000`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Вводить через keyboard/type и обязательно выполнять blur; для short/mixed masked values проверять clear-on-blur и message/state, а не абстрактную невалидность.

## TC-PASSCUR-042

**№:** 42
**Название:** Шестизначный код подразделения
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-011; ATOM-011; ASSERT-PASS-CUR-011; BSR 91

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Допустимое значение: `123456`.

### Шаги

1. Ввести `123456` в поле «Код подразделения».
2. Проверить, что поле отображает введенные шесть цифр в предусмотренном формате.
3. Очистить поле «Код подразделения».

### Итоговый ожидаемый результат

Поле «Код подразделения» отображает введенное значение как `123-456`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-043

**№:** 43
**Название:** Поле «Код подразделения» обязательно для заполнения
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-031; ATOM-031; ASSERT-PASS-CUR-031

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

- Код подразделения: оставить пустым.

### Шаги

1. Оставить поле «Код подразделения» пустым.
2. Нажать кнопку `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Поле подсвечено красным; под полем отображается текст «Обязательно к заполнению».

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PASSCUR-044

**№:** 44
**Название:** Отображение поля «Код подразделения» в блоке «Паспортные данные»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-R2
**Трассировка:** OBL-PASS-CUR-010; ATOM-010; ASSERT-PASS-CUR-010; BSR 90

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Паспортные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля «Код подразделения».

### Итоговый ожидаемый результат

Поле «Код подразделения» отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.
