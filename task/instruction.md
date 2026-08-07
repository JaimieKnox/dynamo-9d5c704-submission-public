The package at `/app/gaegrid` rebuilds generalized advantage estimates for offline
trajectory packs. The tree runs end to end, but graded reports diverge when timeout
truncations, true terminations, and summary mass interact on the same horizon. Repair
the implementation so those interactions match the specification.

Each directory under `/app/packs` is one trajectory pack. `/app/spec/contract.md`,
`/app/spec/pack-format.md`, and `/app/spec/report-schema.md` are normative.

Write one report per pack to `/app/reports/<pack>.json` using the pack directory name.
For every pack under `/app/packs`:

1. The report exists, parses as JSON, and carries `pack`, `steps`, and `summary`.
2. `steps` has one typed entry per index in ascending order.
3. Per-step `advantage` and `return` match the contract to six decimal places.
4. `bootstrapped` is true exactly on truncated indices.
5. Summary counts and means match the contract to six decimal places.

No pack ships an expected report. Only `/app/reports` is graded. You may replace
anything under `/app/gaegrid`.
