# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

The agent inherits a replay auditor for an asynchronous actor-learner reinforcement learning
trainer at `/app/rlaudit`, nine recorded run bundles at `/app/runs`, and a four document
normative contract at `/app/docs`. It must produce one audit document per bundle at
`/app/out/<bundle>.json` holding, per learner step, the target epoch in force, the ordered
slot sequence of accepted draws, the count of rejected draws and four aggregates, plus the
run totals.

The auditor as delivered produces nothing at all: `learner.run_bundle`, the per step replay
orchestration, raises `NotImplementedError`. Rebuilding it from the contract is the bulk of the
task. The module keeps only its imports and `segment_stats`, the glue that feeds one segment
through the V-trace kernel, so the numerical layer is off the table and what has to be derived is
the stateful accounting: cumulative visibility, buffer admission and slot ownership, per step
residency, registration order and seeding, draw rejection, per step re-evaluation under the epoch
in force, deferred priority write back, and the aggregates and totals.

Two of the modules that do survive deviate from the contract, in ways no sample bundle can
expose, so code that arrives looking intact cannot be trusted either:

1. `ingest.load_shards` sorts by `(actor_id, seq)`, keeping each actor's stream contiguous.
   That equals the global admission order only while the actors' sequence ranges do not
   interleave.
2. `ingest.visible_seq` takes the last admission entry at or below the step in file order
   instead of the largest watermark among them. That agrees only while the ingest log is
   written in ascending order, which the bundle format explicitly does not promise.
3. `segments.Segment.residency_index` returns the segment's newest admission index rather
   than its oldest, so entries remain drawable past the point where the ring overwrote their
   first transition. Invisible until the buffer wraps.
4. `segments.build_segments` bootstraps a time limit cut from the observation the cut
   transition was acted from rather than from the recorded `cut_obs_id`. Invisible without
   truncations.

The V-trace kernel (`vtrace.py`), the sampler (`sampler.py`), the buffer (`buffer.py`), the
epoch selection (`params.py`) and the priority expression are already contract faithful, so
rewriting the obvious numerical module changes nothing.

## Why the sample bundles do not settle it

`s01`, `s02` and `s03` are single epoch runs with disjoint in-order shard sequence ranges, one
admission at step 0, fewer transitions than buffer slots, and no time limit truncation. They
exercise segment formation, registration order, the sampler, the V-trace recursion, the weight
normalisation and the write back timing, which is enough to make a fresh orchestration testable,
and none of the four surviving deviations. The six graded bundles stagger visibility, interleave
actor sequence ranges, wrap the buffer, refresh the target part way through and truncate
episodes, so each of them activates several deviations at once. Because sampling is priority
proportional, one wrong decision reroutes every later draw, and the resulting document stays
plausible rather than visibly broken: transitions are all admitted, segments are all registered,
roughly the right number are evicted, and only the drawn sequences and the priority sums are
wrong.

## What the contract does and does not spell out

The stateful rules, stream ordering, cumulative visibility, residency of a segment's
transitions, which epoch snapshot a step evaluates under, and the bootstrap for each cut kind,
are stated as constraints on the asynchronous system. A solver has to turn them into index
arithmetic using ring buffer and target network reasoning, which is the expertise the task
claims to test. Everything an expert could not be expected to infer is spelled out exactly
instead: the sampler and its stream, the V-trace recursion, the importance sampling weight and
its normalisation, the priority expression, the registration tie break, the write back timing,
the aggregate definitions, the run totals, and the output schema with its rounding.

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
performed were: reference and oracle agree on all nine bundles, an auditor that keeps the four
surviving deviations but is otherwise a correct orchestration matches the oracle on the three
sample bundles and differs on all six graded bundles, and a mutation
sweep over every documented rule changes at least one graded bundle, including the residency
comparison at its exact boundary where `n - i == buffer_capacity` and `n - i ==
buffer_capacity + 1` both occur.

## Calibration

    cd task
    harbor run -p . --agent oracle   # reward 1.0
    harbor run -p . --agent nop      # reward 0.0
