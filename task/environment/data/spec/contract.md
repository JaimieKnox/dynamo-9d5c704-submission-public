# timeout-cut return ledger contract (normative)

The package rebuilds timeout-aware λ-returns and advantages for offline trajectory packs.

## Flags and successors

- `terminated=true` ends the episode with no bootstrap. Successor value and non-terminal
  multiplier are both zero for that index.
- When `terminated=false`, the successor value is `value[t+1]` if `t+1` is inside the
  horizon, otherwise `bootstrap_value` from `meta.json`. The non-terminal multiplier is one.
- When both `terminated` and `truncated` are true, termination wins for successors.
- Report field `bootstrapped` is true only when `truncated` is true and `terminated` is false.

Successor resolution lives in the package's successor helper; cut masks must consume it.

## Segments

Each trajectory row carries integer `segment`. The reverse-time λ accumulator must reset to
zero when moving from index `t+1` to `t` if `segment[t] != segment[t+1]`. Flag-driven
non-terminal multipliers still apply inside a segment.

## Recurrence

For each index `t` from the end of the horizon to the start (after any required segment reset):

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * next_nonterminal_t * A_{t+1}`

`R_t = A_t + V_t`

## Summary mass

`mean_advantage` and `mean_return` are importance-weighted averages over every index where
`terminated` is false, using each row's `is_weight`:

`mean = sum_i (is_weight_i * x_i) / sum_i is_weight_i`

Truncated indices remain in the mass when not terminated. If every index is terminated, fall
back to the full horizon with the same weighted formula.
