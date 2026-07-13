# Протокол V3 Bounded Rerun

## Причина

V2 закрыл V1 dictionary/calibration дефекты, но semantic reviewer нашёл два неоднозначных пользовательских действия: альтернативный глагол в `TC-VAMB-004` и неуказанную группу для дублирующегося dictionary value в `TC-VAMB-012`.

## Единственное Изменение Класса

`execution-action-unambiguity`:

- compiler не пропускает group locator из `test_data`, если он отсутствует в исполнимом `planned_check`;
- runner блокирует альтернативные действия вида `установить или сохранить`;
- runner блокирует дублирующееся dictionary value без child group id/name, кроме явно заданной политики `в любой группе`;
- V3 design plan уточняет действие OBL-005 и child path `DICT-101` для OBL-013.

## Неизменяемые Условия

- те же 13 obligations / 12 TC и те же DOCX/XHTML/PDF hashes;
- package v7, backend только `exec`, run profile `benchmark`;
- один fresh writer и один reviewer, один dispatcher invocation;
- без retry/resume/rebind/assisted/sharding/SDK fallback/promotion;
- все V1/V2 output используются только как comparison evidence.

## Gates И Targets

- 13/13 reviewer verdicts `covered`, либо terminal evidence без promotion;
- dictionary completeness и два calibration lifecycle item сохраняются;
- оба V2 action-ambiguity finding больше не воспроизводятся;
- duration `<120 s`, uncached tokens/OBL `<8000`, validator `<=1`, orchestration overhead `<=15%`;
- три protected baseline hashes неизменны, production target отсутствует.

## Terminal Rule

V3 — последний live-запуск этой итерации. Его первый dispatcher invocation завершает эксперимент независимо от результата; последующее исправление относится к новой итерации.
