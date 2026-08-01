Build the forensic ledger for every asynchronous training recording found in `/app/runs`.
The auditor source at `/app/rlaudit` does run, and this assignment is not asking for an
absent component. Its learner iteration is almost right, but interactions between its
successive phases are not faithful. Correct those interactions so replay tells the truth.

Five documents define that truth: `/app/docs/bundle-format.md` describes the recordings,
`/app/docs/learner-contract.md` governs learner state, `/app/docs/comparisons.md` fixes exact
boundary predicates and reductions, `/app/docs/sampler.md` defines draw semantics, and
`/app/docs/output-schema.md` specifies the ledger. All five are normative.

Use each recording directory's basename for a JSON filename under `/app/out`. A submission
is successful precisely when:

1. A corresponding file exists for every run, is valid JSON, and exposes `bundle`, `steps`,
   and `totals` at its root.
2. The step ledger contains the full learner iteration range in increasing order and every
   row conforms to the declared data types.
3. The value of `target_epoch` identifies the target active during its row's iteration.
4. The slot IDs in `sampled` reproduce accepted draws in sequence without collapsing
   repeated IDs.
5. The per-row `dropped_nonresident` number exactly accounts for rejected draws.
6. The quartet of step-level numeric summaries is accurate through six decimal places.
7. Six run-wide counters and the correctly rounded ending priority sum appear in `totals`.

No expected audit document is supplied. The grader reads only generated content in
`/app/out`, and the implementation beneath `/app/rlaudit` may be changed freely.
