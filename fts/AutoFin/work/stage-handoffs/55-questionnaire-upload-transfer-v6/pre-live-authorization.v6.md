# Pre-Live Authorization V6

## Решение

`authorized-one-shot`: пользовательская инструкция `Выполняй v6` разрешает один live benchmark invocation после успешного offline checkpoint. Разрешение не распространяется на production promotion.

## Immutable Binding

| object | SHA-256 / identity |
| --- | --- |
| pushed offline checkpoint | `5135c023f51253fb8dce992b0396942e3e7a37d2` |
| stage package SHA-256 | `8d30cc27da9a16d3c162c76d847b4e4c582d54720273bdcdc502f0f3458ff106` |
| package digest | `c0a6cb07676ca3d7ae3617289dcf4712f100c3ca510a0b4732e58a9b961cb32d` |
| input fingerprint | `f60a5bdf97689cfdcd87860c0c7b55f9199663886cf83ee201c5f3f6b2a13b2c` |
| atomic obligations SHA-256 | `b2e92672e1a528e2bb7597375390dbdf228746540af6dde48b219afd35d4639d` |
| dispatcher config SHA-256 | `14522560aeead43741aae243870bfbe719c5731903ca7d295e5cf5c8430f09a5` |

## Invocation Contract

- backend: verified `exec` only;
- run profile: `benchmark`;
- invocation budget before run: `1`;
- retry/resume/repair/rebind/sharding: prohibited;
- SDK fallback: prohibited;
- manual draft correction: prohibited;
- production target write and promotion: prohibited;
- любой terminal result, включая timeout/backend/validation failure, расходует budget до `0`.

## Authorized Command Shape

`review_cycle_backend_dispatcher.py --backend exec --config <bound-config> --run-profile benchmark`

Selection и performance outputs сохраняются только в V6 review-cycle directory. После вызова разрешён read-only анализ результата и запись terminal handoff artifacts.
