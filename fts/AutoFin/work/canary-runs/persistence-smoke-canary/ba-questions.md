# BA Questions: Persistence Smoke Canary

| id | status | question | why it matters | affected_tc |
| --- | --- | --- | --- | --- |
| `BA-PS-001` | `blocking-for-execution` | What exact UI action saves changes in the application card for section 4.3? | Source rows describe editable fields but do not name a save control or autosave behavior. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-002` | `blocking-for-execution` | After saving, how should a tester leave the card and later return to the same card without discarding changes? | Reopen path through `BSR 35` is source-backed, but exit-after-save flow is not. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-003` | `blocking-for-cleanup` | Should persistence smoke use isolated applications, or should each TC restore changed data in a shared application? | Smoke TC create and modify persistent data; cleanup must not corrupt shared test data. | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-004` | `open` | Is deletion persistence required for added work/home phone rows in addition to contact-person deletion? | Current smoke samples added work-phone persistence and contact-person deletion; phone deletion can be added if required. | follow-up |
