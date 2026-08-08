# Report schema (normative)

Write `/app/artifacts/<pack>.json` as UTF-8 JSON.

Top level keys: `pack` (string), `steps` (array), `summary` (object).

Each `steps[]` object has `index` (int), `advantage` (number, 6 dp), `return` (number,
6 dp), `bootstrapped` (bool, true iff the source index was truncated and not terminated).

`advantage` is the reverse-time accumulator from contract.md.
`return` equals that advantage plus the **raw** `critic_a` at the same index (not the
registered state value used inside the TD residual).

`summary` keys: `horizon`, `truncation_count`, `termination_count` (ints),
`mean_advantage`, `mean_return` (numbers, 6 dp).

`mean_advantage` follows the importance-mass rules in weighting.md.
`mean_return` follows the return-mass rules in weighting.md.
