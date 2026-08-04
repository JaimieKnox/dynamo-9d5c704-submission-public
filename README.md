# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Supporting modules are largely contract faithful. The shipped learner loop is almost
complete but disagrees with lagged visibility, registration-time epoch freeze, and
full-registry importance weight scope. The oracle installs fixed `ingest.py` and
`learner.py`, then runs the CLI. Graded bundles force those three interactions to matter
while sample bundles stay green under the buggy tree.
