# Synthetic Fixture Generation Policy

`scripts/create_randomdatatools_synthetic_fixture.py` — опциональный helper для
одноразового создания нейтральных синтетических test fixtures из
`https://api.randomdatatools.ru/`.

## Назначение

Используй helper, только если текущему тест-дизайну нужны конкретные значения для
свободного ввода или проверки формата, а ФТ, справочник, support и уже имеющиеся
fixtures не дают таких значений. Допустимые примеры: ФИО, телефон, e-mail,
свободный текст, дата, серия/номер паспорта для проверки формата или маски,
уникальное наименование и случайный нейтральный идентификатор.

Это один подключаемый synthetic provider по
[`test-data-source-planning-policy.md`](test-data-source-planning-policy.md),
а не обязательный источник данных и не часть runtime test execution. Для
закрытого справочника используй `DICT-*`; для интеграционного сценария — fixture
того provider-а, чьё поведение проверяется; объекты, роли и статусы в стенде
подготавливаются отдельно.

## One-time lifecycle

1. До написания или уточнения зависимого `TC-*` вызови helper ровно один раз для
   одного нового `FX-SYNTH-*`.
2. Передай конкретную цель (`--purpose`), отбираемые значения
   (`--select имя=путь_в_JSON`) и, при необходимости, проверку формата
   (`--pattern имя=регулярное_выражение`). Helper создаёт новый неизменяемый
   каталог с raw JSON snapshot и `<fixture_id>.fixture.json`.
3. Зафиксируй в `fixture-catalog.md` fixture id, purpose, выбранные literals,
   относительные пути snapshot/receipt и SHA-256. В `TC-*` укажи те же конкретные
   literals; выполнение TC не требует нового API-вызова или чтения API.
4. Не перезаписывай fixture и не делай регулярной live-проверки. Новый вызов
   допускается только по явному запросу на новый synthetic fixture; он создаёт
   новый `FX-SYNTH-*`.

Пример:

```text
python scripts/create_randomdatatools_synthetic_fixture.py --fixture-id FX-SYNTH-CONTACT-001 --purpose "Проверка формата e-mail и телефона" --select email=Email --select phone=Phone --pattern "email=^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$" --output-dir fts/<FT>/work/test-design/<scope>/fixtures/FX-SYNTH-CONTACT-001
```

В текущем profile endpoint поля называются `Email` и `Phone`; имена и набор
полей не считаются стабильным контрактом. Если provider изменил response,
helper должен завершиться без fixture, а не подставлять другой путь или
выдуманное значение.

## Ограничения provenance

Синтетическое значение имеет provenance `synthetic`, а не `source`,
`dictionary`, `verified external` или `DaData`. Его нельзя использовать как
доказательство:

- существования организации или адреса;
- бизнес-валидности ИНН, ОГРН, КПП, БИК или расчётного счёта;
- прохождения контрольного алгоритма продукта;
- результата поиска, автозаполнения или иной интеграции;
- наличия стендовой роли, объекта или статуса.

Для этих случаев TC получает `needs-test-data`, `candidate-ui-calibration` или
source-backed/DaData fixture по соответствующему контракту. Нельзя маскировать
такую зависимость значением из RandomDataTools.

## Review rule

Writer и reviewer проверяют, что `FX-SYNTH-*` используется только для
разрешённого нейтрального поля, его receipt содержит `request_count: 1`,
snapshot SHA-256 и конкретно отобранные literals, а lifecycle запрещает live
вызовы при ручном прогоне и в автотесте. Любая ссылка на текущий live API в
`Предусловия`, `Шаги` или `Итоговый ожидаемый результат` — blocker.
