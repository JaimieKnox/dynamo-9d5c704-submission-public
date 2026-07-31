The replay auditor in `/app/rlaudit` reconstructs what the learner of an asynchronous actor-learner training run did, from that run's recorded actor shards. The package needs to produce correct audit documents for every recorded run.

Each directory under `/app/runs` is one recorded run bundle. `/app/docs/bundle-format.md`, `/app/docs/learner-contract.md`, `/app/docs/sampler.md` and `/app/docs/output-schema.md` are normative and between them state every rule that decides an audit document. The arithmetic kernel in `/app/rlaudit/vtrace.py`, the sampler, the ring buffer, the parameter snapshots and the shard/segment helpers survived. The learner step loop that drives them did not.

Write one audit document per bundle to `/app/out/<bundle>.json`, using the bundle's directory name. For every bundle directory under `/app/runs`:

1. `/app/out/<bundle>.json` exists, parses as JSON, and carries `bundle`, `steps` and `totals` as described in `/app/docs/output-schema.md`.
2. `steps` holds one entry per learner step of that bundle, in ascending step order, with every schema field present and of the declared type.
3. `target_epoch` on each step is the target epoch the contract puts in force for that step.
4. `sampled` on each step is the exact ordered slot sequence of that step's accepted draws, repeats included.
5. `dropped_nonresident` on each step is the exact number of draws that step rejected.
6. `mean_vtrace_target`, `mean_pg_advantage`, `mean_is_weight` and `priority_sum_after` on each step are the contract's values, to six decimal places.
7. `totals` holds the seven run totals the contract defines, the six counts exactly and `priority_sum_final` to six decimal places.

No bundle ships an expected audit document. Only `/app/out` is graded.

You may edit or replace anything under `/app/rlaudit`.
