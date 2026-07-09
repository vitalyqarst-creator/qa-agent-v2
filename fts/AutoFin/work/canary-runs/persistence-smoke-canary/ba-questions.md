# BA Questions: Persistence Smoke Canary

| id | status | question | why it matters | affected_tc |
| --- | --- | --- | --- | --- |
| `BA-PS-001` | `P0 blocking-for-execution` | What exact UI action saves changes in the application card for section 4.3? | Source rows describe editable fields but do not name a save control or autosave behavior. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-002` | `P0 blocking-for-execution` | What observable signal confirms that save succeeded? | Executable TC need a save-success oracle before leaving/reopening the card. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-003` | `P0 blocking-for-execution` | After saving, what happens and how should a tester leave the card without discarding changes? | Reopen checks are not reproducible until exit-after-save behavior is known. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-004` | `P0 blocking-for-execution` | How should the tester reopen the same saved application? | `BSR 35` opens a selected card, but same-application search/select details need calibration. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-005` | `P1 blocking-for-cleanup` | Should persistence smoke use isolated applications, restore changed data, or delete created entities? | Smoke TC create and modify persistent data; cleanup must not corrupt shared test data. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-006` | `P1 blocking-for-execution` | Which application date must be used as `D` for contact-person birth-date calculations: current UI business date, server date, or tester local date? | `TC-AF43-PS-006` uses `D - 30 calendar years`; setup dates must remain valid for the execution date. | `TC-AF43-PS-006`; `TC-AF43-PS-007` setup |
| `BA-PS-007` | `P2 terminology` | Should artifacts use FT term `Отношение к заявителю` if the UI label differs? | Source review found `Отношение к заявителю`; BA/UI should confirm if runtime UI diverges. | `TC-AF43-PS-006`; `TC-AF43-PS-007`; related v4 TC |

Canonical calibration package: `fts/AutoFin/work/calibration/persistence-save-flow/`.

The package expands these questions into BA/UI calibration priorities and TC conversion rules. The persistence smoke TC must remain `candidate-persistence-calibration` until `BA-PS-001`..`BA-PS-005` are answered; `TC-AF43-PS-006` also depends on `BA-PS-006`, and relation-field wording is tracked by `BA-PS-007`.
