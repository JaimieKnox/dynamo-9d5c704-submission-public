# dynamo/audit-replay-learner

Development notes for reviewers. The agent never sees this file.

## Overview

The agent inherits a replay auditor for an asynchronous actor-learner reinforcement learning
trainer at `/app/rlaudit`, nine recorded run bundles at `/app/runs`, and a five document
normative contract at `/app/docs`. It must produce one audit document per bundle at
`/app/out/<bundle>.json` holding, per learner step, the target epoch in force, the ordered slot
sequence of accepted draws, the count of rejected draws and four aggregates, plus the run
totals, plus a `diagnosis` object naming which documented defect the production learner of that
run was carrying and at which step it first shows.

The task has two halves that cannot be done in either order alone.

## Half one: rebuild the orchestration

The auditor as delivered produces nothing at all: `learner.run_bundle`, the per step replay
orchestration, raises `NotImplementedError`. The module keeps only its imports and
`segment_stats`, the glue that feeds one segment through the V-trace kernel, so the numerical
layer is off the table and what has to be derived is the stateful accounting: cumulative
visibility, buffer admission and slot ownership, per step residency, registration order and
seeding, draw rejection, per step re-evaluation under the epoch in force, deferred priority
write back, and the aggregates and totals.

Every other module that ships is contract faithful. There is no planted bug anywhere in
`/app/rlaudit`, so no amount of reading the shipped code against the docs yields anything. The
one decision that used to be a planted bug, which admission index anchors residency, is now
simply absent: `segments.Segment` exposes `start_index` and `complete_index` and the
orchestration has to work out from contract section 3 that residency turns on the oldest
transition, because the oldest is the one the ring overwrites first.

## Half two: diagnose the recorded production ledger

Every bundle ships `production/ledger-digest.json`, the per step ledger digests the production
learner emitted, plus a totals digest. Each production learner had exactly one deviation from
the contract in force for its whole run, drawn from the closed set of seven in
`/app/docs/defect-modes.md`. A digest is the first 16 hex characters of a SHA-256 over an
integerised canonical string, so it commits to a ledger without revealing any of it.

This is what makes the task resistant to an iterate-test-fix loop. A digest mismatch at step
five is equally consistent with the production defect biting at step five and with the solver's
own replay being wrong at step five, and nothing in the environment distinguishes those. There
is no expected output anywhere in the image, so a wrong implementation terminates confidently
rather than being told. Naming the defect requires building each documented deviation as its own
replay and finding which reproduces every recorded digest, which only works once the faithful
replay is already exactly right.

## Assignment and the traps it carries

| bundle | production defect | `first_divergent_step` |
| --- | --- | --- |
| `s01` | `none` | `-1` |
| `s02` | `none` | `-1` |
| `s03` | `none` | `-1` |
| `g01` | `weight_norm_over_all_draws` | `15` |
| `g02` | `residency_by_last_transition` | `-1` |
| `g03` | `truncated_bootstrap_acting_obs` | `0` |
| `g04` | `shard_local_order` | `0` |
| `g05` | `seed_constant_one` | `4` |
| `g06` | `watermark_last_entry` | `11` |

Each of the seven modes is the answer for exactly one group of bundles, so no mode is dead
weight and none can be ruled out a priori. Three traps are deliberate:

1. `g02` diverges **only in its totals digest**. Its step digests match the contract at every
   one of its 28 steps, so `first_divergent_step` is `-1` while the defect is real. A solver who
   infers a clean run from an unbroken run of matching step digests reports `none` and fails.
   `defect-modes.md` states that a mode reproducing every step digest but not the totals digest
   is not reproducing the run.
2. `g01` diverges at step 15 of 24 and `g06` at step 11 of 32. A solver whose own replay is
   subtly wrong earlier than that reports its own bug's step instead, with no signal.
3. Several modes are inert on several bundles, so more than one mode reproduces some runs. The
   documented candidate order, with `none` first, is what makes the answer single valued. This
   is a stated rule rather than a tie the solver has to guess.

## Why the small bundles do not settle it

`s01`, `s02` and `s03` are single epoch runs with disjoint in-order shard sequence ranges, one
admission at step 0, fewer transitions than buffer slots, and no time limit truncation. Every
one of the six non trivial defect modes is inert on all three, which is why their diagnosis is
`none` and why matching all their digests confirms only the core recursion, the sampler, the
weight normalisation and the write back timing. The six `g` bundles stagger visibility,
interleave actor sequence ranges, wrap the buffer, refresh the target part way through and
truncate episodes. Because sampling is priority proportional, one wrong decision reroutes every
later draw, and the resulting document stays plausible rather than visibly broken.

## What the contract does and does not spell out

Every rule the verifier enforces is written down, including the digest construction, the
candidate order and the totals digest requirement. The stateful rules, stream ordering,
cumulative visibility, residency of a segment's transitions, which epoch snapshot a step
evaluates under, and the bootstrap for each cut kind, are stated as constraints on the
asynchronous system, so a solver has to turn them into index arithmetic using ring buffer and
target network reasoning. Everything an expert could not be expected to infer is spelled out
exactly: the sampler and its stream, the V-trace recursion, the importance sampling weight and
its normalisation, the priority expression, the registration tie break, the write back timing,
the aggregate definitions, the run totals, the digest canonicalisation and the output schema
with its rounding. The difficulty is meant to survive full disclosure, so nothing was made vague
to make it harder.

## Environment

`python:3.13-slim-bookworm` pinned by digest, pure standard library at run time, `pytest` and
`pytest-json-ctrf` baked for the verifier. No GPU, no network dependency, no sidecar service.
Oracle runtime is well under a minute.

## Verification

`tests/test_outputs.py` has one function per numbered success criterion of `instruction.md`.
Expectations are recomputed at verify time by `tests/reference.py`, an independent single file
implementation of the contract and of all seven defect modes, written from the documents rather
than from the oracle, reading `tests/inputs`, the verifier's own copy of the bundle inputs
including the recorded digests. Reading from that copy rather than from `/app/runs` means
expectations cannot be shifted by editing agent visible inputs. Integers, the drawn slot
sequences, `first_divergent_step` and `defect` are compared exactly, the four aggregates and
`priority_sum_final` with absolute tolerance 1e-6.

Development scripts are not part of the submission. The checks they performed were:

- The reference and the oracle agree on all nine documents including the diagnosis.
- Every documented mode is active on at least one graded bundle and inert on all three small
  ones, and every bundle's diagnosis resolves to a single mode under the documented candidate
  order with no accidental collision between two active modes.
- Every episode belongs to one actor with `seq` ascending in `t`, so "first transition" and
  "lowest admission index" cannot disagree and the contract's wording is unambiguous.
- A mutation sweep over the documented rules. Mutating the residency comparison by one slot
  (detected on `g04`), swapping the registration tie break, applying write back immediately,
  shifting the target epoch by a step, changing the terminated bootstrap away from zero,
  counting draws instead of distinct positions, and anchoring eviction on a segment's newest
  transition are all detected on at least one graded bundle by the exact integer fields alone.
  Five of the six graded bundles reach both residency boundary ages, `n - i == buffer_capacity`
  and `n - i == buffer_capacity + 1`.
- The one mutation **not** detected is relaxing the sampler's strict `target < acc` to
  `target <= acc`. That needs a draw target to land exactly on a cumulative priority sum in
  float64, which never happens, so both readings select identical draws. A solver who reads it
  either way passes, which is permissive rather than unfair.

## Calibration

    cd task
    harbor run -p . --agent oracle   # reward 1.0
    harbor run -p . --agent nop      # reward 0.0
