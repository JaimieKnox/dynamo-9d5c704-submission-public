# dynamo/audit-replay-learne

Development notes for reviewers. The agent never sees this file.

## Overview

Rebuild the missing learner step loop of a replay auditor for an asynchronous
actor-learner reinforcement learning trainer so every recorded run bundle unde
`/app/runs` produces a contract-faithful audit document at `/app/out/<bundle>.json`.

## Approach

Supporting modules (buffer, ingest, segments, sampler, params, vtrace) are contract
faithful. `learner.run_bundle` raises `NotImplementedError`. The oracle installs a
complete orchestration and runs the CLI. Graded bundles wrap the ring early and draw
multi-draw batches so residency, write-back timing and weight scope must compose.
