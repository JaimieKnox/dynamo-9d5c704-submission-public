# timeout-cut return ledger contract (normative)

Rebuild timeout-aware lambda-returns for offline packs. Read every file under `/app/spec/`.
Stream registration, seam freezes, truncation residency, eligibility cuts, and mass algebra
are split across the other spec files. No single file restates the full pipeline.

## Flags

- `terminated=true` zeros successor value and non-terminal multiplier.
- Dual-flag rows prefer termination. `bootstrapped` is true only for pure truncations.

## Recurrence

After registration and successor resolution, walk `t` from the end of the horizon to the
start. Clear the lambda accumulator on segment changes before updating index `t`. Let `r_t`
be the scale-adjusted reward at `t`.

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * eligibility_t * A_{t+1}`

`R_t = A_t + V_t`

`V_t` is the registered `critic_a` stream. `V_next_t` and `eligibility_t` follow the other
spec files.
