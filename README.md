# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

The agent inherits a replay auditor for an asynchronous actor-learner reinforcement learning
trainer at `/app/rlaudit`, nine recorded run bundles at `/app/runs`, and a four document
normative contract at `/app/docs`. It must produce one audit document per bundle at
`/app/out/<bundle>.json` holding, per learner step, the target epoch in force, the ordered
slot sequence of accepted draws, the count of rejected draws and four aggregates, plus the
run totals.

The auditor as delivered reconciles perfectly against the three bundles that ship an
`expected.json`, so the environment never signals wrongness. It deviates from the contract in
five places, all in the stateful layers rather than in the arithmetic:

1. `ingest.load_shards` concatenates shard files instead of merging on the global `seq`.
2. `ingest.visible_seq` ignores the admission step, so the whole run is admitted at step 0.
3. `buffer.TransitionBuffer.is_resident` never expires a slot, so no draw is ever rejected
   and evicted segments are served from whatever now occupies their slots.
4. `segments.materialize` reads a run of adjacent buffer slots rather than the episode's own
   transitions, which only coincides while the actors are not interleaved.
5. `learner.run_bundle` caches per segment values and importance ratios at registration and
   reuses them after a target refresh, and treats a time limit cut as an environment
   termination when choosing the bootstrap.

The V-trace kernel (`vtrace.py`), the sampler (`sampler.py`), the epoch selection
(`params.py`) and the priority expression are already contract faithful, so rewriting the
obvious numerical module changes nothing.

## Why the sample bundles stay green

`s01`, `s02` and `s03` are single epoch runs with disjoint in-order shard sequence ranges, one
admission at step 0, fewer transitions than buffer slots, and no time limit truncation. Every
one of the five deviations is dormant under those conditions. The six graded bundles each
activate several of them, and because sampling is priority proportional, one wrong decision
reroutes every later draw.

## Environment

`python:3.13-slim-bookworm` pinned by digest, pure standard library at run time, `pytest` and
`pytest-json-ctrf` baked for the verifier. No GPU, no network dependency, no sidecar service.
Oracle runtime is well under a minute.

## Verification

`tests/test_outputs.py` has one function per numbered success criterion of `instruction.md`.
Expectations are recomputed at verify time by `tests/reference.py`, an independent single file
implementation of the contract written from the documents rather than from the oracle, reading
`tests/inputs`, the verifier's own copy of the bundle inputs. Reading from that copy rather
than from `/app/runs` means expectations cannot be shifted by editing agent visible inputs.
Integers and the drawn slot sequences are compared exactly, the four aggregates and
`priority_sum_final` with absolute tolerance 1e-6.

`gen/` scripts used during development are not part of the submission. The checks they
performed were: reference and oracle agree on all nine bundles, the shipped auditor matches
the oracle on the three sample bundles and differs on all six graded bundles, and a mutation
sweep over every documented rule changes at least one graded bundle, including the residency
comparison at its exact boundary where `n - i == buffer_capacity` and `n - i ==
buffer_capacity + 1` both occur.

## Calibration

    cd task
    harbor run -p . --agent oracle   # reward 1.0
    harbor run -p . --agent nop      # reward 0.0
