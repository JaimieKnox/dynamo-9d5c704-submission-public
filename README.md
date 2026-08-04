# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Ordinary visibility, window formation, and in-batch write-back isolation are already
faithful in the shipped tree. Graded failures come from delayed registration, lagged
sampler priorities versus current importance weights, and resident-scoped priority
seeding under ring wrap. The oracle replaces ingest, buffer, segments, and learner,
then runs the CLI. Sample bundles set the new delays to zero and keep a large ring.
