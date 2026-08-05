# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Epoch attachment, importance-weight snapshots, and deferred write-back are already
contract-faithful. Graded failures come from using the latest admission index for
residency, padding lagged sampler rows with ones, and sorting same-step registration
by earliest-then-latest. The oracle replaces ingest, buffer, segments, and learner,
then runs the CLI. Sample bundles null the delays, use a large ring, and keep batch
size one so those interactions stay green there.
