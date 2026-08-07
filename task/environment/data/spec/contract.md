# timeout-cut return ledger contract (normative)

Rebuild timeout-aware lambda-returns for offline packs. Read every file under `/app/spec/`.
Field meanings and mass algebra are in `pack-format.md`.

## Flags

- `terminated=true` zeros successor value and non-terminal multiplier.
- Non-terminated rows keep non-terminal multiplier one when a bootstrap path applies.
- Dual-flag rows prefer termination. `bootstrapped` is true only for pure truncations.

## Recurrence

After stream registration and successor resolution, walk `t` from the end of the horizon to
the start. Clear the lambda accumulator when `segment[t] != segment[t+1]` before updating
index `t`.

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * next_nonterminal_t * A_{t+1}`

`R_t = A_t + V_t`
