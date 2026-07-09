# Тест-кейсы: раздел 4.3, карточка «Заявка», адреса и контакты клиента

**FT package:** `AutoFin`
**Режим:** independent wide canary, fresh generation
**Canonical output:** `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary.md`
**Основной источник:** `fts/AutoFin/source/FT4AutoFinFinal.docx`
**Machine-readable source:** `fts/AutoFin/source/FT4AutoFinFinal.xhtml`
**PDF cross-check:** `fts/AutoFin/source/FT4AutoFinFinal.pdf`
**Package notes:** `fts/AutoFin/AGENT-NOTES.md`

## Границы покрытия

В scope включены строки таблицы 7 раздела 4.3 по блокам адресов и контактов клиента: `BSR 115`-`BSR 189`.

Внутренние рабочие пакеты:

| package_id | focus | source rows |
| --- | --- | --- |
| `WP-01` | Адрес регистрации клиента | Table 7 rows 33-57, `BSR 115`-`BSR 137` |
| `WP-02` | Адрес фактического места жительства | Table 7 rows 45-57, `BSR 138`-`BSR 161` |
| `WP-03` | Контакты клиента | Table 7 rows 59-64, `BSR 162`-`BSR 172` |
| `WP-04` | Контактные лица | Table 7 rows 66-73, `BSR 173`-`BSR 189` |

Вне scope оставлены персональные данные клиента до `BSR 115`, сведения о занятости, документы, участники, визуальная оценка и действия карточки заявки после выбранных строк. Эти области имеют самостоятельные блоки и отдельные правила.

## Canonical Artifact Links

- Source and scope inventory: `fts/AutoFin/work/canary-runs/independent-wide-canary/source-scope-inventory.md`
- Coverage matrix: `fts/AutoFin/work/canary-runs/independent-wide-canary/coverage-matrix.md`
- Coverage gaps and BA questions: `fts/AutoFin/work/canary-runs/independent-wide-canary/coverage-gaps.md`
- Reviewer notes: `fts/AutoFin/work/canary-runs/independent-wide-canary/reviewer-notes.md`
- Evaluation report: `fts/AutoFin/work/canary-runs/independent-wide-canary/canary-evaluation-report.md`

## Краткое резюме

Сгенерировано 38 ручных тест-кейсов. Набор покрывает видимость, значения по умолчанию, DaData-сценарии с указанными в ФТ подсказками, разложение адресов, состав ручного адреса, маски телефонов, email, условное отображение контактных телефонов, добавление и удаление контактного лица, перечень отношений и ветку «Иное».

Ограничения покрытия вынесены в work artifacts: точные UI-механизмы отклонения значений для числовых/текстовых/date restrictions не додумывались, если ФТ задает только класс ограничения без наблюдаемой реакции.

