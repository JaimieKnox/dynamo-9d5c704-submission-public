# timeout-cut return ledger contract (normative)

The package rebuilds timeout-aware λ-returns and advantages for offline trajectory packs.

## Flags

- `terminated=true` ends the episode with no bootstrap value. The next value is zero and
  the non-terminal multiplier is zero for that index.
- `truncated=true` with `terminated=false` is a timeout cut. The next value is the following
  stored value when the cut is not the final index, otherwise `bootstrap_value` from meta.
  The non-terminal multiplier stays one so the λ-return uses that bootstrap rather than hard zero.
- When both `terminated` and `truncated` are true on the same index, termination wins: next
  value and non-terminal multiplier are both zero. `bootstrapped` in the report is true only
  when `truncated` is true and `terminated` is false.

## Horizon values

Per-index `value` entries cover indices `0 .. horizon-1` only. There is no stored
`value[horizon]`. The reverse-time step that needs a successor value past the final index
must read `bootstrap_value` from `meta.json`.

## Recurrence

For each index `t` from the end of the horizon to the start:

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * next_nonterminal_t * A_{t+1}`

`R_t = A_t + V_t`

`V_next_t` and `next_nonterminal_t` follow the flag rules above.

## Summary mass

`mean_advantage` and `mean_return` average over every index where `terminated` is false.
Truncated indices remain in the mass. If every index is terminated, fall back to the full
horizon.
