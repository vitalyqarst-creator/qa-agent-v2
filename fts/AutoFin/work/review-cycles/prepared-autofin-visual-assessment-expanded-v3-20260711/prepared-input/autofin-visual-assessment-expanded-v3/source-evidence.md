# Prepared Source Evidence

- package_id: `autofin-visual-assessment-expanded-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-visual-assessment-expanded-v3-20260711/prepared-input/.autofin-visual-assessment-expanded-v3.compiled-evidence.md`
- source_sha256: `1818e9ba0a677bfdad8cc1ce061d246684070fcbbb84b1ecc195f9f99b978b36`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## OBL-001

- obligation: OBL-001 | WP-01 | SRC-002.P01 | ATOM-001 | field-property | field-visible | Поле `Визуальная информация` отображается всегда. | SRC-001`; `SRC-002`; `BSR 311 | TC-VAC-001 | covered | Прямая visibility obligation.
- atom: ATOM-001 | WP-01 | SRC-002.P01 | BSR 311 | SRC-001; SRC-002 | Поле `Визуальная информация` отображается всегда. | visibility | covered | TC-VAC-001 | TC-VAC-001 | none_required:covered

- plan: PLAN-001 | WP-01 | visibility | SRC-001; SRC-002; BSR 311 | ATOM-001 | Поле `Визуальная информация` отображается всегда. | positive | visibility | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-001 | covered

## OBL-002

- obligation: OBL-002 | WP-01 | SRC-002.P02 | ATOM-002 | default-value | default-no | Значение по умолчанию равно `Нет`. | SRC-002`; `BSR 312 | TC-VAC-002 | covered | Observable initial state.
- atom: ATOM-002 | WP-01 | SRC-002.P02 | BSR 312 | SRC-002 | Для поля `Визуальная информация` значение по умолчанию равно `Нет`. | default-value | covered | TC-VAC-002 | TC-VAC-002 | none_required:covered

- plan: PLAN-002 | WP-01 | default-value | SRC-002; BSR 312 | ATOM-002 | Для поля `Визуальная информация` значение по умолчанию равно `Нет`. | positive | default-value | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-002 | covered

## OBL-003

- obligation: OBL-003 | WP-01 | SRC-002.P03 | ATOM-003 | dependency | yes-triggers-list | Выбор `Да` является условием показа параметров визуальной оценки. | SRC-002`; `BSR 313 | TC-VAC-003 | covered | Positive trigger.
- atom: ATOM-003 | WP-01 | SRC-002.P03 | BSR 313 | SRC-002 | Выбор `Да` в поле `Визуальная информация` является условием показа параметров визуальной оценки. | dependency-trigger | covered | TC-VAC-003 | TC-VAC-003 | none_required:covered

- plan: PLAN-003 | WP-01 | dependency-trigger | SRC-002; BSR 313 | ATOM-003 | Выбор `Да` в поле `Визуальная информация` является условием показа параметров визуальной оценки. | positive | dependency-trigger | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-003 | covered

## OBL-004

- obligation: OBL-004 | WP-01 | SRC-003.P01 | ATOM-004 | conditional-visibility | list-visible-when-yes | При `Визуальная информация = Да` отображается список параметров. | SRC-003`; `BSR 314 | TC-VAC-004 | covered | Positive visibility branch.
- atom: ATOM-004 | WP-01 | SRC-003.P01 | BSR 314 | SRC-003 | При `Визуальная информация = Да` отображается список `Параметры визуальной оценки`. | conditional-visibility-positive | covered | TC-VAC-004 | TC-VAC-004 | none_required:covered

- plan: PLAN-004 | WP-01 | conditional-visibility-positive | SRC-003; BSR 314 | ATOM-004 | При `Визуальная информация = Да` отображается список `Параметры визуальной оценки`. | positive | conditional-visibility-positive | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-004 | covered

## OBL-005

- obligation: OBL-005 | WP-01 | SRC-003.P02 | ATOM-005 | conditional-visibility | list-hidden-otherwise | Когда значение не равно `Да`, список параметров не отображается. | SRC-003`; `BSR 314 | TC-VAC-005 | covered | Inverse visibility branch.
- atom: ATOM-005 | WP-01 | SRC-003.P02 | BSR 314 | SRC-003 | Когда `Визуальная информация` не равна `Да`, список `Параметры визуальной оценки` не отображается. | conditional-visibility-inverse | covered | TC-VAC-005 | TC-VAC-005 | none_required:covered

- plan: PLAN-005 | WP-01 | conditional-visibility-inverse | SRC-003; BSR 314 | ATOM-005 | Когда `Визуальная информация` не равна `Да`, список `Параметры визуальной оценки` не отображается. | positive | conditional-visibility-inverse | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-005 | covered

## OBL-006

- obligation: OBL-006 | WP-01 | SRC-003.P03 | ATOM-006 | table-list | dictionary-hierarchy-shown | Список использует восемь категорий и их значения из `DICT-001`. | SRC-003-SRC-052`; `BSR 315`; `DICT-001 | TC-VAC-006 | covered | Parent dictionary expands to eight stable child category rows.
- atom: ATOM-006 | WP-01 | SRC-003.P03 | BSR 315; DICT-001 | SRC-003-SRC-052 | `Параметры визуальной оценки` использует активные группы и значения из `DICT-001`. | table-list | covered | TC-VAC-006 | TC-VAC-006 | none_required:covered

- plan: PLAN-006 | WP-01 | table-list | SRC-003-SRC-052; BSR 315; DICT-001 | ATOM-006 | `Параметры визуальной оценки` использует активные группы и значения из `DICT-001`. | positive | table-list | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-006 | covered

## OBL-007

- obligation: OBL-007 | WP-01 | SRC-003.P04 | ATOM-007 | checkbox-list | value-has-checkbox | Каждое обычное значение `DICT-001` доступно как checkbox. | SRC-005-SRC-050`; `BSR 315`; `DICT-001 | TC-VAC-007 | covered | Checkbox composition.
- atom: ATOM-007 | WP-01 | SRC-003.P04 | BSR 315; DICT-001 | SRC-005-SRC-050 | Каждое обычное значение критерия из `DICT-001` доступно как checkbox value. | checkbox-list | covered | TC-VAC-007 | TC-VAC-007 | none_required:covered

- plan: PLAN-007 | WP-01 | checkbox-list | SRC-005-SRC-050; BSR 315; DICT-001 | ATOM-007 | Каждое обычное значение критерия из `DICT-001` доступно как checkbox value. | positive | checkbox-list | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-007 | covered

## OBL-008

- obligation: OBL-008 | WP-01 | SRC-003.P05 | ATOM-008 | requiredness | one-selection-required | Для параметров визуальной оценки требуется минимум одно выбранное значение. | SRC-003`; `BSR 316 | TC-VAC-008 | covered | Required-selection obligation.
- atom: ATOM-008 | WP-01 | SRC-003.P05 | BSR 316 | SRC-003 | Для `Параметры визуальной оценки` требуется минимум одно выбранное значение. | requiredness | covered | TC-VAC-008 | TC-VAC-008 | none_required:covered

- plan: PLAN-008 | WP-01 | requiredness | SRC-003; BSR 316 | ATOM-008 | Для `Параметры визуальной оценки` требуется минимум одно выбранное значение. | positive | requiredness | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-008 | covered

## OBL-009

- obligation: OBL-009 | WP-01 | SRC-003.P06 | ATOM-009 | conditional-visibility | other-shows-comment | Checkbox `Другое` отображает текстовое поле комментария. | SRC-009`; `SRC-019`; `SRC-024`; `SRC-030`; `SRC-036`; `SRC-043`; `SRC-050`; `BSR 317`; `DICT-001 | TC-VAC-009 | covered | `CAT-008` remains standalone comment-only.
- atom: ATOM-009 | WP-01 | SRC-003.P06 | BSR 317; DICT-001 | SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050 | Выбор checkbox `Другое` в блоке отображает текстовое поле комментария. | other-comment-field-display | covered | TC-VAC-009 | TC-VAC-009 | none_required:covered

- plan: PLAN-009 | WP-01 | other-comment-field-display | SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; BSR 317; DICT-001 | ATOM-009 | Выбор checkbox `Другое` в блоке отображает текстовое поле комментария. | positive | other-comment-field-display | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-009 | covered

## OBL-010

- obligation: OBL-010 | WP-01 | SRC-003.P07 | ATOM-010 | requiredness | other-comment-required | Комментарий для выбранного `Другое` обязателен. | SRC-009`; `SRC-019`; `SRC-024`; `SRC-030`; `SRC-036`; `SRC-043`; `SRC-050`; `BSR 317`; `DICT-001 | TC-VAC-010 | covered | Requiredness obligation.
- atom: ATOM-010 | WP-01 | SRC-003.P07 | BSR 317; DICT-001 | SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050 | Комментарий для выбранного `Другое` обязателен. | other-comment-field-requiredness | covered | TC-VAC-010 | TC-VAC-010 | none_required:covered

- plan: PLAN-010 | WP-01 | other-comment-field-requiredness | SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; BSR 317; DICT-001 | ATOM-010 | Комментарий для выбранного `Другое` обязателен. | positive | other-comment-field-requiredness | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-010 | covered

## OBL-011

- obligation: OBL-011 | WP-01 | SRC-010.P01 | ATOM-011 | field-property | standalone-comment-distinct | Standalone-строки `Комментарий` являются отдельными полями ввода и не смешиваются с `Другое`. | SRC-010`; `SRC-020`; `SRC-051`; `SRC-052 | TC-VAC-011 | covered | `GAP-001` is closed and omitted from active package gaps.
- atom: ATOM-011 | WP-01 | SRC-010.P01 | GAP-001:closed | SRC-010; SRC-020; SRC-051; SRC-052 | Standalone rows `Комментарий` являются отдельными полями ввода и не смешиваются с checkbox `Другое`. | standalone-comment-input | covered | TC-VAC-011 | TC-VAC-011 | GAP-001:closed

- plan: PLAN-011 | WP-01 | standalone-comment-input | SRC-010; SRC-020; SRC-051; SRC-052; GAP-001:closed | ATOM-011 | Standalone rows `Комментарий` являются отдельными полями ввода и не смешиваются с checkbox `Другое`. | positive | standalone-comment-input | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-011 | covered

## OBL-012

- obligation: OBL-012 | WP-01 | SRC-010.P02 | ATOM-012 | field-property | standalone-comment-editable | Standalone-поле `Комментарий` принимает введённый текст. | SRC-010`; `SRC-020`; `SRC-051`; `SRC-052 | TC-VAC-012 | covered | `GAP-001` is closed and omitted from active package gaps.
- atom: ATOM-012 | WP-01 | SRC-010.P02 | GAP-001:closed | SRC-010; SRC-020; SRC-051; SRC-052 | Standalone поле `Комментарий` принимает введенный текст. | standalone-comment-input-edit | covered | TC-VAC-012 | TC-VAC-012 | GAP-001:closed

- plan: PLAN-012 | WP-01 | standalone-comment-input-edit | SRC-010; SRC-020; SRC-051; SRC-052; GAP-001:closed | ATOM-012 | Standalone поле `Комментарий` принимает введенный текст. | positive | standalone-comment-input-edit | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-012 | covered

## OBL-013

- obligation: OBL-013 | WP-01 | SRC-003.P08 | ATOM-013 | checkbox-list | multiple-selection | В checkbox list можно одновременно выбрать несколько обычных значений. | SRC-002`; `SRC-003`; `SRC-005-SRC-050`; `BSR 313`; `BSR 315`; `DICT-001 | TC-VAC-013 | covered | Multiple-selection obligation.
- atom: ATOM-013 | WP-01 | SRC-002.P04; SRC-003.P08 | BSR 313; BSR 315; DICT-001 | SRC-002; SRC-003; SRC-005-SRC-050 | В checkbox list можно выбрать несколько обычных значений критериев. | checkbox-list-multiple-selection | covered | TC-VAC-013 | TC-VAC-013 | none_required:covered

- plan: PLAN-013 | WP-01 | checkbox-list-multiple-selection | SRC-002; SRC-003; SRC-005-SRC-050; BSR 313; BSR 315; DICT-001 | ATOM-013 | В checkbox list можно выбрать несколько обычных значений критериев. | positive | checkbox-list-multiple-selection | field-state | See linked `TC-*` expected result; one observable UI state per case. | DOCX/PDF source artifacts and closed analyst clarification where referenced. | TC-VAC-013 | covered

## DICT-001

DICT-001 | Параметры визуальной оценки | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | DICT-101`; `DICT-102`; `DICT-103`; `DICT-104`; `DICT-105`; `DICT-106`; `DICT-107`; `DICT-108 | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Parent inventory row; child category rows preserve the complete source values.

## DICT-101

DICT-101 | Признаки алкоголика | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`; `Отечность, нездоровый цвет лица, синяки под глазами`; `Шатающаяся походка, несвязная речь, сильно трясутся руки`; `Неадекватная реакция на задаваемые вопросы, плохая ориентация во времени`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | GAP-001:closed | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-102

DICT-102 | Признаки наркомана | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Длинные, спущенные рукава в любую погоду, отрешенный взгляд`; `Неоправданно резкие перемены настроения`; `Отечность, нездоровый цвет лица, синяки под глазами`; `Следы многочисленных уколов на кистях`; `Неестественно суженные / расширенные зрачки`; `Шатающаяся походка, несвязная речь, плохая координация движений`; `Неприятный запах кислоты`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | GAP-001:closed | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-103

DICT-103 | Признаки бывшего заключенного | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Татуировки уголовного содержания на кистях, пальцах (например, с изображением перстней, крестов, четырех точек, образующих квадрат с пятой точкой посередине и др.)`; `Характерный для заключенных жаргон`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-104

DICT-104 | Признаки «преображенного» бомжа | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Несоответствие внешнего вида Клиента данным, которые он указывает в анкете (например, в анкете указано, что Клиент - гендиректор крупной организации, однако состояние зубов, волос, лица или кистей рук говорит о том, что ему полностью безразличны его внешний вид и здоровье)`; `Признаки алкоголика / наркомана / бывшего заключенного`; `Несоответствие размеров / стиля одежды`; `Сильный макияж / использует парик`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-105

DICT-105 | Поведенческие признаки потенциального неплательщика | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Клиент не может внятно объяснить, откуда он узнал о Банке / для чего ему необходим кредит, при этом испытывает волнение / раздражение`; `Мнимые семейные пары, часто с детьми (например Клиент называет свою "супругу" Надей, а в штампе паспорта имя супруги - Елена); неадекватная реакция на вопросы о супруге / детях`; `Сильное волнение клиента в ходе анкетирования, особенно при ответах на дополнительные / уточняющие вопросы`; `Слишком заострено внимание на последствиях неплатежей`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-106

DICT-106 | Сопровождение Клиента | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Клиент находится в сопровождении подозрительных лиц, осуществляющих подсказки по заполнению анкеты`; `Клиент находится в сопровождении подозрительных лиц, осуществляющих давление на Клиента`; `Клиент использовал "шпаргалку" при заполнении анкеты`; `Клиент неоднократно звонил по телефону для выяснения ответов на вопросы анкеты`; `Клиент замечен в сопровождении лиц, ранее приводивших мошенников / подставных лиц для получения кредитов`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-107

DICT-107 | Признаки подделки документов | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Заметны следы подчистки документов, химического травления текста`; `Заметны следы подделки подписей, оттисков печатей и штампов`; `Наличие в документах дописок, допечаток, исправлений, орфографических ошибок`; `Личность заемщика не может быть достоверно подтверждена (заемщик явно не похож по фотографии)`; `Заметны следы замены фотографии в паспорте, листов в многостраничных документах`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.

## DICT-108

DICT-108 | Прочие признаки (комментарий обязателен) | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | none_required:standalone-comment-only | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | GAP-001:closed | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`.
