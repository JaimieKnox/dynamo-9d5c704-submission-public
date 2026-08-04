# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Delayed registration, lagged sampler draws, and ledger-wide seeding are already
faithful in the shipped tree. Graded failures come from attaching the completion-step
epoch instead of the insert-step epoch, computing importance weights from the sampler
draw vector, and committing priority write-backs mid-batch. The oracle replaces ingest,
buffer, segments, and learner, then runs the CLI. Sample bundles keep both delays at
zero and batch size one so those interactions stay silent.
