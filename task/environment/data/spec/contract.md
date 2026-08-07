# timeout-cut return ledger contract (normative)

The package rebuilds timeout-aware λ-returns and advantages for offline trajectory packs.

## Flags

- `terminated=true` ends the episode with no bootstrap value. The next value is zero and
  the non-terminal multiplier is zero for that index.
- `truncated=true` (and `terminated=false`) is a timeout cut. The next value is the following
  value entry (or `bootstrap_value` from meta when the cut is the final index). The
  non-terminal multiplier stays one so the λ-return uses that bootstrap rather than hard zero.


For a truncated index that is not the final horizon index, the following step's stored value is the bootstrap source.
## Recurrence

For each index `t` from the end of the horizon to the start:

`delta_t = r_t + gamma * V_{t+1} * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * next_nonterminal_t * A_{t+1}`

`R_t = A_t + V_t`

`V_{horizon}` is `bootstrap_value` from `meta.json`.

## Summary mass

`mean_advantage` and `mean_return` average over every index where `terminated` is false.
Truncated indices remain in the mass. If every index is terminated, fall back to the full
horizon.
