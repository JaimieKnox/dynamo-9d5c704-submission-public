# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Visibility lag, truncation cut observation, and deferred write-back are already
faithful. Graded failures come from completing-transition residency, completion-step
epoch attachment under register_delay, and resident-only importance-weight mass. The
oracle replaces ingest, buffer, segments, and learner, then runs the CLI.
