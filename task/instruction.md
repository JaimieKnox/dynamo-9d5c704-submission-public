Repair `/app/cutreturn` so offline trajectory traces produce contract-true timeout-aware
lambda-return reports. The installed tree finishes every trace, but graded artifacts still diverge
from the normative specs under mixed cuts.

Read every file under `/app/spec/`. Trace directories live under `/app/traces`.

Emit `/app/artifacts/<trace>.json` for each trace directory name. Every artifact must:

1. Parse as JSON with top-level `pack`, `steps`, and `summary`.
2. Contain one ascending `steps` row per index.
3. Match contract `advantage` and `return` values to six decimals.
4. Set `bootstrapped` true only for truncated indices that are not terminated.
5. Match summary counts and means to the contract (six decimals for means).

Do not expect goldens inside the traces. Only `/app/artifacts` is graded. You may rewrite
`/app/cutreturn`.
