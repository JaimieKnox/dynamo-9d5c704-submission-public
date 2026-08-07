# timeout-cut return ledger contract (normative)

Rebuild timeout-aware λ-returns for offline packs. Read every file under `/app/spec/`.

## Flags

- `terminated=true` zeros the successor value and non-terminal multiplier.
- `truncated=true` with `terminated=false` keeps a bootstrap path (non-terminal = 1).
- When both flags are true, termination wins. Report `bootstrapped` only for pure truncations.

## Recurrence

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * next_nonterminal_t * A_{t+1}`

`R_t = A_t + V_t`

`V_t` is the registered baseline critic. `V_next_t` follows the successor rules in the other
spec files. Horizon length is `meta.horizon` with stored raw values on `0 .. horizon-1` only.