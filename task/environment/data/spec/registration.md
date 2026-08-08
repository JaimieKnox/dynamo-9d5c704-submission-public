# Critic registration (normative)

Each row has raw `critic_a` and `critic_b`.

A registered stream of lag `L` and fill `init` must satisfy:
- registered[t] equals raw[t - L] when that source index exists and shares `segment[t]`
- registered[t] equals `init` when the source is missing or lies in a different segment

`critic_a` uses (`lag_a`, `init_a`). `critic_b` uses (`lag_b`, `init_b`).

The TD residual's state value is the registered `critic_a` stream. Indices where that register
reads `init` are value-pad indices and cut eligibility and both summary mass sets.

Bootstrap reads: segment-edge freezes and interior `t+1` successors use registered `critic_b`.
Mid-segment truncation residency uses raw `critic_b` as in segments.md.
