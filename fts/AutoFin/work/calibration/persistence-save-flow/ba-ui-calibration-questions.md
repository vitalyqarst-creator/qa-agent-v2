# BA/UI calibration questions: persistence save flow

## BA-PS-001 - Exact save action

**Priority:** P0
**Question:** Какое точное действие пользователь выполняет для сохранения изменений карточки заявки в разделе 4.3?
**Needed for TC:** `TC-AF43-PS-001`..`TC-AF43-PS-007`
**Blocks:** removal of `candidate-persistence-calibration`
**Possible answers to confirm:** кнопка, автосохранение, сохранение при переходе, другое действие.

## BA-PS-002 - Save success oracle

**Priority:** P0
**Question:** Как пользователь понимает, что сохранение прошло успешно?
**Needed for TC:** `TC-AF43-PS-001`..`TC-AF43-PS-007`
**Blocks:** executable expected result after save.

## BA-PS-003 - Exit-after-save flow

**Priority:** P0
**Question:** Что происходит после сохранения и каким source-backed действием пользователь выходит из карточки?
**Needed for TC:** `TC-AF43-PS-001`..`TC-AF43-PS-007`
**Blocks:** reproducible save/reopen execution.

## BA-PS-004 - Reopen same application

**Priority:** P0
**Question:** Как пользователь повторно открывает ту же заявку после сохранения?
**Known source:** `BSR 35` confirms opening a selected application card; exact search/select route to the same saved application still needs calibration.
**Needed for TC:** `TC-AF43-PS-001`..`TC-AF43-PS-007`
**Blocks:** reproducible after-reopen oracle.

## BA-PS-005 - Cleanup / isolation

**Priority:** P1
**Question:** Какой cleanup strategy использовать: изолированная заявка, восстановление исходных данных или удаление созданных сущностей?
**Needed for TC:** all persistence TC.
**Blocks:** safe execution on shared environments.

## BA-PS-006 - Current application date source

**Priority:** P1
**Question:** Что считается текущей датой приложения `D` для TC с датой рождения контактного лица?
**Needed for TC:** `TC-AF43-PS-006`.
**Blocks:** deterministic execution of rolling date data.

## BA-PS-007 - Relation field terminology

**Priority:** P2
**Question:** Какой source-backed термин использовать в artifacts: `Отношение к клиенту` или `Отношение к заявителю`?
**Needed for TC:** `TC-AF43-PS-006` and related v4 TC.
**Current source review decision:** `Отношение к заявителю` is source-backed by section 4.3; this question remains for BA/UI confirmation if UI labels differ from FT.
