# timeout-cut return ledger contract (normative)

Rebuild timeout-aware lambda-returns for offline packs. Read every file under `/app/spec/`.
No single file is a complete implementation recipe. Registration, successors, eligibility,
scales, baselines, and mass each constrain a different slice of the ledger.

Flags: termination zeros successor channels. `bootstrapped` is true only for pure truncations.

After registration and successor resolution, walk `t` from the end. Form a TD residual with
discount `gamma` against the registered state value, then a reverse-time accumulator whose
discount is `gamma_lambda` (defaulting to `gamma`) and whose per-index lambda may come from
`segment_lambdas` when that array is present. Eligibility cuts are not the same predicate as
successor non-terminal factors; see segments.md and the shared eligibility helper contract.

Emitted per-index `advantage` is the reverse-time accumulator. Emitted per-index `return` adds
a baseline that is not always the same stream used inside the TD residual; see report-schema.md.
