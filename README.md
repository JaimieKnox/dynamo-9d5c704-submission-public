# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Ring boundary inclusivity, truncated cut observations, pre-draw importance mass, and
deferred write-back are already contract-faithful. Graded failures come from applying
publication lag with the wrong sign, scoring under the live step epoch, and sorting
same-step registration by first-then-final admission. The oracle replaces ingest,
buffer, segments, and learner, then runs the CLI. Sample bundles null publication lag
and freeze a single target epoch so those interactions stay green there.
