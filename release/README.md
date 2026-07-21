# Release Profiles

Проект использует один исходный commit и два детерминированных профиля сборки.

## Qualification

`qualification-manifest.json` включает runtime, инструкции, тесты и curated
benchmark configs. Сырые прогоны, diagnostics, stage/review work и оригинальные
AutoFin DOCX/XHTML/PDF/mockups исключены. Активный `PostFinal-v2` и используемые
макеты связаны с профилем только путями и SHA-256; сами файлы остаются локальными.
Небольшие воспроизводимые DaData-fixtures входят в qualification-профиль.
Проверка локальных входов выполняется с `--require-local-inputs`.

```powershell
python scripts/build_release_bundle.py `
  --manifest release/qualification-manifest.json `
  --check-only `
  --require-local-inputs
```

## Production

`production-manifest.json` включает runtime package, необходимые entrypoints,
skills и canonical references. Он fail-closed запрещает `evals/`, `tests/`,
`fts/`, work/output/tmp и бинарные исходники.

```powershell
python scripts/build_release_bundle.py `
  --manifest release/production-manifest.json `
  --output dist/ft-test-case-agent-production
```

Output directory обязан быть новым. В корне bundle создаётся
`release-manifest.json` с SHA-256 каждого файла и общим `tree_sha256`.

Benchmark profile не превращается в отдельную кодовую ветку. Production bundle
строится из того же commit/tag, поэтому исправления runtime и quality gates не
расходятся между qualification и production.
