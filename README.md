# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct replay auditor for an asynchronous actor-learner reinforcement
learning trainer so every recorded run bundle under `/app/runs` produces a contract
faithful audit document at `/app/out/<bundle>.json`.

## Approach

The shipped package looks complete. Short sample runs never wrap the replay buffer and
use a single draw per step, so several shared-state defects stay inert there. Graded
runs wrap the ring early, draw larger batches, and force residency, priority seeding and
write-back timing to interact. The oracle replaces the ring-buffer / priority registry
and the learner orchestration with contract-faithful versions, then runs the CLI.
