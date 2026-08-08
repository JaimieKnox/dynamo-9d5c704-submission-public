# timeout-cut return ledger contract (normative)

Rebuild timeout-aware lambda-returns for offline packs. Read every file under `/app/spec/`.
The other files state invariants for registration, successors, eligibility, scales, and mass.
Together they determine a unique ledger; no single file is a complete implementation recipe.

Flags: termination zeros successor channels. `bootstrapped` is true only for pure truncations.

Recurrence after registration and successor resolution, walking `t` from the end:

`delta_t = r_t + gamma * V_next_t * next_nonterminal_t - V_t`

`A_t = delta_t + gamma * lambda * eligibility_t * A_{t+1}`

`R_t = A_t + V_t`

where `r_t` is the effective scale-adjusted reward and `V_t` is registered `critic_a`.
Eligibility is defined with the successor and truncation invariants in segments.md.
