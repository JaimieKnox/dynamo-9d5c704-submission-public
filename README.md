# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct asynchronous actor-learner replay auditor so every recorded run
bundle under `/app/runs` produces a contract-faithful audit document at
`/app/out/<bundle>.json`.

## Approach

Ingest visibility and full-registry weight scope are already faithful in the shipped
tree. The remaining defects are compositional: in-batch priority visibility, attached
scoring-epoch retargeting on resident segments, and illegal end-of-episode window
segments. The oracle replaces `ingest.py`, `segments.py`, and `learner.py`, then runs
the CLI. Sample bundles keep batch size one and a single scoring epoch so those
interactions stay green under the buggy tree.
