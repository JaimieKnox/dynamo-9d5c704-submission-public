# dynamo/audit-replay-learne

Development notes for reviewers. The agent never sees this file.

## Overview

Repair a near-correct replay auditor for an asynchronous actor-learner reinforcement
learning trainer so every recorded run bundle under `/app/runs` produces a contract
faithful audit document at `/app/out/<bundle>.json`.

## Approach

The shipped `/app/rlaudit` package looks complete and reconciles the three sample bundles
that ship `expected.json`. Silent boundary defects remain in ingest ordering, watermark
aggregation, residency anchoring, truncated bootstrap observation choice, insert priority
seeding and importance weight normalisation. Those defects are inert on the sample bundles
and active on the six graded ones.

## Environment

Python 3.13 slim image with pytest baked in. Inputs under `/app/runs`, docs unde
`/app/docs`, package under `/app/rlaudit`.

## Verification

Oracle and an independent `tests/refpkg` reference derive expectations from `tests/inputs`.
Exact match on slots and counts, 1e-6 on the four aggregates and `priority_sum_final`.
