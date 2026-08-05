The replay auditor in `/app/rlaudit` reconstructs what the learner of an asynchronous
actor-learner training run did from recorded actor shards. The package runs end to end,
but graded ledgers diverge when ring residency, delayed registration eligibility, and
importance-weight pooling interact under wrap and lag. Repair the implementation so
those interactions match the docs.

Each directory under `/app/runs` is one recorded run bundle. `/app/docs/bundle-format.md`,
`/app/docs/learner-contract.md`, `/app/docs/comparisons.md`, `/app/docs/sampler.md`, and
`/app/docs/output-schema.md` are normative and together state every rule that decides an
audit document.

Write one audit document per bundle to `/app/out/<bundle>.json`, using the bundle directory
name. For every bundle under `/app/runs`:

1. The document exists, parses as JSON, and carries `bundle`, `steps`, and `totals`.
2. `steps` has one correctly typed entry per learner step in ascending order.
3. `target_epoch` is the reported epoch in force for that step.
4. `sampled` is the exact ordered slot sequence of accepted draws, repeats included.
5. `dropped_nonresident` is the exact rejected-draw count.
6. The four per-step floating aggregates match the contract to six decimal places.
7. `totals` contains the six exact counts and rounded final priority sum.

No bundle ships an expected audit document. Only `/app/out` is graded. You may replace
anything under `/app/rlaudit`.
