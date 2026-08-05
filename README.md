# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Visibility lag, carried scoring epochs, and ledger-length importance weights are already
faithful. Graded failures come from truncated-segment bootstrap choice, using sampler
draw mass for importance weights, and committing priority write-backs mid-batch. The
oracle replaces ingest, buffer, segments, and learner, then runs the CLI. Sample bundles
keep delays at zero and batch size one so those interactions stay silent.
