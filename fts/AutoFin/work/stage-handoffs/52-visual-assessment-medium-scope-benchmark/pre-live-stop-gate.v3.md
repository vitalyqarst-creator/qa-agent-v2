# Pre-Live Stop Gate V3

## Current Status

`blocked-before-live`

## Разрешённый Следующий Шаг

1. Commit and push the bounded code/tests, V2 terminal evidence and immutable V3 package/config.
2. Verify local/origin SHA equality and all package/config/baseline hashes.
3. Create, commit and push a separate `pre-live-authorization.v3.md`.
4. Invoke exactly one V3 dispatcher with backend `exec` and profile `benchmark`.

## Запрещено

- live before both pushes;
- any package/config/code change after authorization;
- retry/resume/rebind/repair/assisted/sharding/SDK fallback;
- production promotion or baseline mutation;
- any further live in this iteration after V3 invocation.
