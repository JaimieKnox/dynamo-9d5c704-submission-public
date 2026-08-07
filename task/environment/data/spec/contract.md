# timeout-cut return ledger contract (normative)

Rebuild timeout-aware lambda-returns for offline packs. Read every file under `/app/spec/`.
Field meanings, dual critic streams, timeout residency, eligibility cuts, scales, and mass
algebra are in `pack-format.md`, `registration.md`, `segments.md`, and `weighting.md`.

## Flags

`terminated` and `truncated` are independent. Prefer termination when both are true for
successor channels. `bootstrapped` is true only when `truncated` is true and `terminated`
is false.

## Recurrence

After stream registration and successor resolution, walk `t` from the end of the horizon to
the start. Clear the lambda accumulator when `segment[t] != segment[t+1]` before updating
index `t`. Let `r_t` be the scale-adjusted reward at `t`.

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * ell_t * A_{t+1}`

`R_t = A_t + V_t`

`V_t` is the registered `critic_a` stream. `V_next_t` and `next_nonterminal_t` follow the
successor rules. `ell_t` is the eligibility factor from `segments.md` (zero on truncated
rows).
