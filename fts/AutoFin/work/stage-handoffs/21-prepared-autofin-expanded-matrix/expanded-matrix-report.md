# Expanded AutoFin Prepared Compiler Matrix

## Boundary

- FT package: `fts/AutoFin` only.
- Source family: `FT4AutoFinFinal.docx/xhtml/pdf` only.
- Live execution and production promotion: not started.

## Built Packages

| class | scope | obligations | active gaps | dictionaries | route |
| --- | --- | ---: | ---: | ---: | --- |
| simple field/cardinality | widget selection | 6 | 2 | 0 | `simple-field-property` |
| reset/state | search clear | 4 | 0 | 0 | `standard-required` |
| generated document/dependency | print form | 21 | 6 | 5 | `standard-required` |
| action navigation | common actions | 1 | 0 | 0 | `standard-required` |
| summary/navigation | calculator summary | 4 | 1 | 0 | `standard-required` |
| hierarchical dictionary/checkbox/dependency | visual assessment | 13 | 0 | 9 | `standard-required` |

The visual-assessment dictionary contains one parent `DICT-001` and eight unique child category ids. The compiler recursively includes the child rows in prepared evidence.

## Deliberately Blocked Migration Candidates

| class | scope | blocker |
| --- | --- | --- |
| numeric/length/integration | client addresses | Legacy obligation table covers only deep classes; 27 atomic rows have no obligation. Two stale obligation-to-plan links were corrected before this broader debt became visible. |
| file upload/async/persistence | documents and questionnaire files | One obligation exists for 47 atoms; 46 atomic rows require semantic obligation projection. |
| external recognition/dictionary | document recognition popup | Legacy placeholder `OBL-N/A-001` has no atom and a noncanonical status. |

These failures are matrix results, not compiler defects. Automatically inventing the missing obligations would make the benchmark green while weakening traceability.

## Routing Improvements

- `yes_with_evidence` and `yes_with_fixture` are accepted only as evidence-qualified standard routes.
- Obligation property types independently force standard routing for navigation, dependency, numeric, file upload, integration, persistence, generated documents and repeatable lifecycle.
- An applicability matrix using generic `other` can no longer hide an action-navigation obligation in the fast path.

## Next Gate

The six built packages are sufficient for the next promotion-off live canary selection. The three blocked legacy scopes should be migrated package-by-package, not in the same live experiment.
