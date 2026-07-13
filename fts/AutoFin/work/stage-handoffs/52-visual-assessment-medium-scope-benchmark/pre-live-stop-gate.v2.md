# Pre-Live Stop Gate V2

## Current Status

`blocked-before-live`

## Почему Live Пока Запрещён

Package v7, config, protocol, runtime-profile fix and pre-live evidence must first be committed and pushed as one immutable checkpoint. A separate authorization artifact must then bind the pushed commit and all relevant hashes.

## Разрешённый Следующий Шаг

1. Stage only project-owned V2 artifacts and the bounded runtime-profile regression.
2. Commit and push the checkpoint; verify local and remote SHA equality.
3. Create, commit and push `pre-live-authorization.v2.md` in a separate commit.
4. Invoke exactly one dispatcher with backend `exec` and no SDK fallback.

## Запрещено

- live before both pushes;
- changing package, config or runtime profile after authorization;
- retry/resume/rebind/repair/assisted mode/sharding;
- promotion or write to any FT-first baseline;
- using V1 draft/reviewer output as requirement evidence.
