# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Visibility postponement and registration ordering are faithful in the shipped tree.
Graded failures come from attaching scoring epochs at completion instead of delayed
insert, using residency-filtered IS mass, and first-wins repeated write-back. The
verifier derives sealed expectations then grades without importing the oracle. The
oracle replaces fixed modules and runs the CLI.
