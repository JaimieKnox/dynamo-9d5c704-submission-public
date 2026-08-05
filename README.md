# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Earliest-index residency, current-priority lag padding, and latest-first registration
order are already contract-faithful. Graded failures come from ignoring visibility_lag
in ingest, scoring accepted draws under the live step epoch, and using resident-only
N in importance weights. The oracle replaces ingest, buffer, segments, and learner,
then runs the CLI. Sample bundles null visibility lag, freeze a single target epoch,
and keep a large ring so those interactions stay green there.
