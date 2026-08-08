# Report schema (normative)

Write `/app/artifacts/<pack>.json` as UTF-8 JSON.

Top level keys: `pack` (string), `steps` (array), `summary` (object).

Each `steps[]` object has `index` (int), `advantage` (number, 6 dp), `return` (number,
6 dp), `bootstrapped` (bool, true iff the source index was truncated and not terminated).

`summary` keys: `horizon`, `truncation_count`, `termination_count` (ints),
`mean_advantage`, `mean_return` (numbers, 6 dp).

`mean_advantage` follows the importance-mass rules in weighting.md.
`mean_return` is the unweighted arithmetic mean of per-index returns over all non-terminated
indices (or the full horizon if every index is terminated). Importance membership and `w_snap`
do not apply to `mean_return`.
