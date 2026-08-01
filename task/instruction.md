Recorded actor activity is available as run bundles beneath `/app/runs`. Turn each bundle
into a faithful account of the learner's execution. The existing implementation in
`/app/rlaudit` is already complete enough to execute; the defect lies in near-correct
interactions among phases of its learner step loop. Bring those phase relationships into
agreement with the specification rather than treating this as a missing-module exercise.

The rules of record are distributed across `/app/docs/bundle-format.md`,
`/app/docs/learner-contract.md`, `/app/docs/sampler.md`, and
`/app/docs/output-schema.md`. Read them as a single contract when deciding how replay state
evolves and how the result is represented.

For a bundle directory named `NAME`, place the resulting JSON at
`/app/out/NAME.json`. Grading checks these seven properties:

1. Every recorded bundle has a valid JSON object containing the top-level members
   `bundle`, `steps`, and `totals`.
2. Its `steps` array is ordered by learner-step number, has exactly one entry for every
   such step, and uses the schema's required value types.
3. Each step reports the applicable epoch in `target_epoch`.
4. Each `sampled` array preserves the precise order of accepted slot draws, including
   duplicate slots.
5. Each `dropped_nonresident` value equals the number of draws rejected at that step.
6. All four floating-point summaries for a step are correct at six-decimal precision.
7. The final `totals` object gives all six counters exactly and the terminal priority sum
   rounded as specified.

There is no expected audit document included with any bundle. Evaluation considers only
the files produced in `/app/out`. Changes anywhere within `/app/rlaudit` are permitted.
