# timeout-cut return ledger contract (normative)

Rebuild timeout-aware lambda-returns for offline packs. Read every file under `/app/spec/`.
Registration, successors, eligibility, scales, baselines, and mass each constrain a different
slice. Do not treat any one file as a complete recipe.

Termination zeros successor channels. `bootstrapped` is true only for pure truncations.

Walk `t` from the end after registration and successor resolution. Form a TD residual against
the registered state value. The residual's discount may be segment-local when `segment_gammas`
is present; otherwise it is pack `gamma`. The reverse-time accumulator always discounts with
`gamma_lambda` (defaulting to pack `gamma`) and may use `segment_lambdas` for the lambda factor.

Successor magnitudes on some cut paths are not used raw in the residual; segments.md states
when the effective reward scale also multiplies `V_next` before the residual is formed.

Emitted `advantage` is the reverse-time accumulator. Emitted `return` adds the raw `critic_a`
baseline (report-schema.md). Summary means follow weighting.md, including scale-scoring that
applies only when computing `mean_advantage`.
