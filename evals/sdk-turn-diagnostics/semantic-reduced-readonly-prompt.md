# Reduced semantic review diagnostic

This is a read-only diagnostic. Do not edit files. Do not update cycle-state.yaml.
Do not create reviewer artifacts. Do not recursively read directories.

Goal: inspect whether a bounded semantic review turn can complete.

Read only these files:

- fts/ft-2-OF_17/test-cases/section-31-client-documents-upload-and-actuality.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/package-test-design-plan.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/coverage-map.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/atomic-requirements-ledger.md

Return a short Markdown response only:

1. `status: complete`
2. Count visible executable TC headings.
3. List up to five missing or suspicious traceability links, if any.
4. List up to five test-design quality concerns, if any.
5. Stop.
