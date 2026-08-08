# Report schema (normative)

Write `/app/artifacts/<pack>.json` as UTF-8 JSON.

Top level keys: `pack`, `steps`, `summary`.

Each `steps[]` object has `index`, `advantage`, `return` (6 dp), `bootstrapped`.

`advantage` is the reverse-time accumulator (not scale-scored for the summary).
`return` equals that advantage plus raw `critic_a` at the same index.

`summary` keys: `horizon`, `truncation_count`, `termination_count`, `mean_advantage`,
`mean_return`. Means follow weighting.md.
