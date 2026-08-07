# timeout-cut return ledger contract (normative)

Rebuild timeout-aware λ-returns for offline packs. Cut masks feed a reverse-time
recurrence. Read every file under `/app/spec/` before changing code.

## Flags

- `terminated=true` zeros the successor value and non-terminal multiplier.
- `truncated=true` with `terminated=false` keeps a bootstrap path (non-terminal = 1).
- When both flags are true, termination wins. Report `bootstrapped` only for pure truncations.

## Recurrence

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * next_nonterminal_t * A_{t+1}`

`R_t = A_t + V_t`

`V_t`, `V_next_t`, segment handling, and summary mass follow the other normative files in
`/app/spec/`. Horizon length is `meta.horizon` with stored values on `0 .. horizon-1` only.