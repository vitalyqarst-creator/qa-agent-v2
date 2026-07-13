# Pre-Live Stop Gate

## Current Status

`blocked-before-live`

## Почему Live Пока Запрещён

Prepared package, config and validation evidence must first be committed and pushed as an immutable checkpoint. A second, explicit authorization artifact must then bind the pushed commit, package id/version/digest, config hash and production-boundary hashes.

## Разрешённый Следующий Шаг

1. Stage only project-owned H52 artifacts, the immutable prepared package and the bounded validator fix/test.
2. Commit and push the checkpoint; verify local and remote SHA equality.
3. Create, commit and push `pre-live-authorization.md` in a separate commit.
4. Invoke exactly one dispatcher with backend `exec` and no SDK fallback.

## Запрещено

- live before both pushes;
- changing package or config after authorization;
- retry/resume/rebind/repair/assisted mode/sharding;
- promotion or write to existing FT-first baselines;
- treating missing `ui-evidence-policy` fixtures as evidence about this benchmark's semantics.
